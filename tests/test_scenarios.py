import json

import pytest

import scenarios
from scenarios import ScenarioError, dump, load, plan_matches, session_updates

SETTINGS = {
    "country": "TR", "timeframe": "Monthly", "default_cogs": 10.0, "capacity": 0, "import_share": 30,
    "model_kind": "loglog", "use_real": True, "use_trend": True, "product": "Kahve", "max_price": 120.0,
    "variable_fees": 15.0,
    "prices_incl_vat": True, "vat_rate": 20.0, "max_change": 15.0, "ending": ".99", "comp_match_cut": 50,
    "comp_match_rise": 0, "shock_infl": 29.5, "shock_usd_infl": 3.7, "shock_fx": 18.5, "shock_passthrough": False,
    "test_step": 10.0,
}
PLAN = {"test_price": 65.37, "current_price": 59.43, "weeks": 4, "actual": [310.0, None, 298.0, 371.0]}
DATA = {"sha256": "ab" * 32, "file_name": "satislar.xlsx", "product": "Kahve"}


def doc(**overrides) -> bytes:
    d = json.loads(dump(SETTINGS, PLAN, DATA))
    d.update(overrides)
    return json.dumps(d).encode()


def test_round_trip_keeps_settings_plan_and_data():
    raw = dump(SETTINGS, PLAN, DATA)
    loaded = load(raw)
    assert loaded.settings == SETTINGS and loaded.test_plan == PLAN and loaded.data == DATA
    assert loaded.warnings == [] and loaded.saved_at
    assert "Kahve" in raw.decode("utf-8")  # readable UTF-8, not \\u escapes


def test_dump_ignores_unknown_keys_and_casts_numpy_like_values():
    import numpy as np

    raw = dump({**SETTINGS, "lang": "tr", "secret": "x", "shock_infl": np.float64(12.5)}, None, DATA)
    settings = json.loads(raw)["settings"]
    assert "lang" not in settings and "secret" not in settings and settings["shock_infl"] == 12.5


def test_unknown_mistyped_and_out_of_range_values():
    d = json.loads(doc())
    d["settings"].update({"hacker": "rm -rf", "country": "XX", "variable_fees": "lots", "use_real": 1,
                          "import_share": 150, "shock_fx": -80.0, "capacity": 2.5, "max_change": float("nan")})
    loaded = load(json.dumps(d).encode())
    s = loaded.settings
    assert s["import_share"] == 100 and s["shock_fx"] == -50.0  # clipped
    for key in ("hacker", "country", "variable_fees", "use_real", "capacity", "max_change"):
        assert key not in s
    keys = {w.key: w.params["keys"] for w in loaded.warnings}
    assert set(keys) == {"scen_warn_dropped", "scen_warn_clipped"}
    assert "import_share" in keys["scen_warn_clipped"] and "hacker" in keys["scen_warn_dropped"]


@pytest.mark.parametrize("old,expected,warned", [
    ({"commission": 15.0, "payment_fee": 2.0}, 17.0, set()),
    ({"commission": 12.5}, 12.5, set()),
    ({"commission": 80.0, "payment_fee": 20.0}, 90.0, {"scen_warn_clipped"}),
    ({"commission": 15.0, "payment_fee": "two"}, None, {"scen_warn_dropped"}),
])
def test_legacy_commission_and_payment_fee_are_summed(old, expected, warned):
    d = json.loads(doc(schema=1))
    del d["settings"]["variable_fees"]
    d["settings"].update(old)
    loaded = load(json.dumps(d).encode())
    assert loaded.settings.get("variable_fees") == expected
    assert "commission" not in loaded.settings and "payment_fee" not in loaded.settings
    assert {w.key for w in loaded.warnings} == warned
    assert all("commission" not in w.params.get("keys", "") for w in loaded.warnings)


@pytest.mark.parametrize("raw,key", [
    (b"not json {", "scen_err_invalid"),
    (b"\xff\xfe\x00", "scen_err_invalid"),
    (json.dumps({"app": "other", "settings": {}}).encode(), "scen_err_not_ours"),
    (json.dumps([1, 2]).encode(), "scen_err_not_ours"),
])
def test_files_that_are_not_scenarios_are_rejected(raw, key):
    with pytest.raises(ScenarioError) as err:
        load(raw)
    assert err.value.args[0].key == key


def test_newer_schema_warns_but_loads():
    loaded = load(doc(schema=scenarios.SCHEMA + 1))
    assert [w.key for w in loaded.warnings] == ["scen_warn_newer"] and loaded.settings == SETTINGS


def test_damaged_test_plan_is_dropped_with_warning():
    loaded = load(doc(test_plan={"test_price": 1, "current_price": 1, "weeks": 3, "actual": [1, 2]}))
    assert loaded.test_plan is None and [w.key for w in loaded.warnings] == ["scen_warn_plan_invalid"]
    assert load(doc(test_plan=None)).warnings == []


def test_plan_matching():
    assert plan_matches(PLAN, 65.37, 59.43, 4)
    assert not plan_matches(PLAN, 66.00, 59.43, 4)
    assert not plan_matches(PLAN, 65.37, 59.43, 6)
    assert not plan_matches(None, 65.37, 59.43, 4)


def test_session_updates_map_runtime_keys():
    updates = session_updates(load(dump(SETTINGS, None, DATA)), current_country="US")
    assert updates["vat_TR"] == 20.0 and "vat_rate" not in updates  # VAT widget of the loaded country
    assert updates["_pending_max_price"] == 120.0 and updates["_pending_product"] == "Kahve"
    assert updates["shock_country"] == "TR" and updates["shock_infl"] == 29.5
    assert "max_price" not in updates and "product" not in updates


def test_empty_cost_override_round_trips_as_null():
    loaded = load(dump({**SETTINGS, "cost_override": None}, None, DATA))
    assert "cost_override" in loaded.settings and loaded.settings["cost_override"] is None
    assert loaded.warnings == []
    assert load(dump({**SETTINGS, "cost_override": 0.0}, None, DATA)).settings["cost_override"] == 0.0


@pytest.mark.parametrize("schema, expected", [(1, None), (2, None), (scenarios.SCHEMA, 0.0)])
def test_old_zero_cost_override_meant_not_set(schema, expected):
    d = json.loads(doc(schema=schema))
    d["settings"]["cost_override"] = 0
    assert load(json.dumps(d).encode()).settings["cost_override"] == expected
    d["settings"]["cost_override"] = 12.5  # a real override is kept from any schema
    assert load(json.dumps(d).encode()).settings["cost_override"] == 12.5


def test_file_format_round_trips_and_unknown_formats_are_dropped():
    assert load(dump({**SETTINGS, "file_format": "dmy_comma"}, None, DATA)).settings["file_format"] == "dmy_comma"
    d = json.loads(doc())
    d["settings"]["file_format"] = "yyyy/dd/mm"
    loaded = load(json.dumps(d).encode())
    assert "file_format" not in loaded.settings and loaded.warnings
