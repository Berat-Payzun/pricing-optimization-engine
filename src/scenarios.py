"""Saved scenarios: the app's settings, and a running price test, as a JSON file the user keeps.

Files are downloaded and uploaded by the user rather than stored on the server: Streamlit
Community Cloud's disk is wiped on restart and shared by every visitor. The sales data itself
is not saved, only a fingerprint of it, so the app can warn when a scenario is loaded against
a different file. Loading only ever parses JSON (no code runs) and every value is checked
against SETTINGS: unknown keys are dropped, out-of-range numbers clipped.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime

from config import COUNTRY_MAP, PERIOD_MULT
from optimizer import ENDINGS
from translations import Msg

APP_ID = "pricing-optimization-engine"
SCHEMA = 2


@dataclass(frozen=True)
class Setting:
    kind: type  # bool, int, float or str
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None


# Every user input, by its widget key. Inputs with a widget key that changes at runtime are
# saved under a stable name instead: "vat_rate" (widget vat_<country>) and "max_price"
# (widget max_price_<model>_<product>_<months>). The display language is the viewer's own
# preference and is not saved.
SETTINGS: dict[str, Setting] = {
    "drop_dupes": Setting(bool),
    "country": Setting(str, choices=tuple(COUNTRY_MAP)),
    "timeframe": Setting(str, choices=tuple(PERIOD_MULT)),
    "default_cogs": Setting(float, 0.0),
    "cost_override": Setting(float, 0.0),
    "fixed_monthly": Setting(float, 0.0),
    "capacity": Setting(int, 0),
    "import_share": Setting(int, 0, 100),
    "model_kind": Setting(str, choices=("auto", "linear", "loglog")),
    "use_real": Setting(bool),
    "use_season": Setting(bool),
    "use_trend": Setting(bool),
    "product": Setting(str),
    "max_price": Setting(float, 0.01),
    "variable_fees": Setting(float, 0.0, 90.0),
    "prices_incl_vat": Setting(bool),
    "vat_rate": Setting(float, 0.0, 50.0),
    "extra_unit_cost": Setting(float, 0.0),
    "max_change": Setting(float, 0.0, 100.0),
    "min_margin": Setting(float, 0.0, 95.0),
    "price_floor": Setting(float, 0.0),
    "price_ceiling": Setting(float, 0.0),
    "ending": Setting(str, choices=ENDINGS),
    "comp_match_cut": Setting(int, 0, 100),
    "comp_match_rise": Setting(int, 0, 100),
    "shock_infl": Setting(float, -10.0, 100.0),
    "shock_usd_infl": Setting(float, -10.0, 100.0),
    "shock_fx": Setting(float, -50.0, 100.0),
    "shock_comp": Setting(float, -50.0, 50.0),
    "shock_passthrough": Setting(bool),
    "test_step": Setting(float, 1.0, 30.0),
}


class ScenarioError(ValueError):
    pass


@dataclass
class Loaded:
    settings: dict
    test_plan: dict | None
    data: dict  # sha256, file_name, product of the sales file it was saved with
    saved_at: str
    warnings: list[str] = field(default_factory=list)


def dump(settings: dict, test_plan: dict | None, data: dict) -> bytes:
    """Serialise the known settings (others are ignored) to a JSON file's bytes."""
    clean = {}
    for key, rule in SETTINGS.items():
        if settings.get(key) is not None:
            clean[key] = rule.kind(settings[key])
    doc = {
        "app": APP_ID,
        "schema": SCHEMA,
        "saved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "data": data,
        "settings": clean,
        "test_plan": test_plan,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False).encode("utf-8")


def _check(value, rule: Setting):
    """(value, clipped) if `value` fits the rule, or None if it can't be used."""
    if rule.kind is bool:
        return (value, False) if isinstance(value, bool) else None
    if rule.kind is str:
        if not isinstance(value, str) or (rule.choices is not None and value not in rule.choices):
            return None
        return value, False
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    if rule.kind is int and value != int(value):
        return None
    number = rule.kind(value)
    clipped = min(max(number, rule.lo if rule.lo is not None else number), rule.hi if rule.hi is not None else number)
    return rule.kind(clipped), clipped != number


def _test_plan(raw) -> dict | None:
    """The saved price test, or None if it's missing or malformed."""
    if not isinstance(raw, dict):
        return None
    try:
        weeks = int(raw["weeks"])
        actual = [None if a is None else float(a) for a in raw["actual"]]
        plan = {"test_price": float(raw["test_price"]), "current_price": float(raw["current_price"]),
                "weeks": weeks, "actual": actual}
    except (KeyError, TypeError, ValueError):
        return None
    return plan if len(actual) == weeks and all(a is None or math.isfinite(a) for a in actual) else None


def _migrate(settings: dict) -> dict:
    """Schema 1 saved marketplace commission and payment fee as two inputs; they are now one sum.
    A value that isn't a number is passed on so it is dropped with a warning."""
    settings = dict(settings)
    old = [settings.pop(k) for k in ("commission", "payment_fee") if k in settings]
    if old and "variable_fees" not in settings:
        bad = [v for v in old if _check(v, Setting(float)) is None]
        settings["variable_fees"] = bad[0] if bad else float(sum(old))
    return settings


def load(raw: bytes) -> Loaded:
    """Parse and validate a scenario file. Raises ScenarioError if it isn't one."""
    try:
        doc = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ScenarioError(Msg("scen_err_invalid")) from None
    if not isinstance(doc, dict) or doc.get("app") != APP_ID or not isinstance(doc.get("settings"), dict):
        raise ScenarioError(Msg("scen_err_not_ours"))

    warnings: list[str] = []
    if not isinstance(doc.get("schema"), int) or doc["schema"] > SCHEMA:
        warnings.append(Msg("scen_warn_newer"))

    settings, dropped, clipped = {}, [], []
    for key, value in _migrate(doc["settings"]).items():
        checked = _check(value, SETTINGS[key]) if key in SETTINGS else None
        if checked is None:
            dropped.append(str(key))
            continue
        settings[key], was_clipped = checked
        if was_clipped:
            clipped.append(key)
    if dropped:
        warnings.append(Msg("scen_warn_dropped", keys=", ".join(dropped[:8])))
    if clipped:
        warnings.append(Msg("scen_warn_clipped", keys=", ".join(clipped[:8])))

    test_plan = _test_plan(doc.get("test_plan"))
    if doc.get("test_plan") is not None and test_plan is None:
        warnings.append(Msg("scen_warn_plan_invalid"))
    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    return Loaded(settings, test_plan, data, str(doc.get("saved_at", "")), warnings)


def session_updates(loaded: Loaded, current_country: str | None) -> dict:
    """The Streamlit session-state writes that apply a loaded scenario. Settings whose widget key
    changes at runtime go to the matching key (VAT) or to a _pending_ key the app applies when
    it draws that widget (max price, product). Setting shock_country to the loaded country stops
    the app from resetting the loaded shock sliders to live data."""
    values = dict(loaded.settings)
    updates = {}
    country = values.get("country", current_country)
    if "vat_rate" in values and country:
        updates[f"vat_{country}"] = values.pop("vat_rate")
    for name in ("max_price", "product"):
        if name in values:
            updates[f"_pending_{name}"] = values.pop(name)
    updates.update(values)
    if "country" in values:
        updates["shock_country"] = values["country"]
    return updates


def plan_matches(saved: dict | None, test_price: float, current_price: float, weeks: int) -> bool:
    """Whether a saved price test is the same test as the one the app has built now."""
    return (saved is not None and saved["weeks"] == weeks
            and abs(saved["test_price"] - test_price) < 0.005 and abs(saved["current_price"] - current_price) < 0.005)
