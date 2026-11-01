import pickle
import re
import string
from pathlib import Path

import pytest

from translations import LANGUAGES, STRINGS, Msg, localize, translate

SRC = Path(__file__).resolve().parents[1] / "src"


def fields(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


def test_every_key_has_all_languages():
    for key, entry in STRINGS.items():
        assert set(entry) == set(LANGUAGES), key
        assert all(entry[lang].strip() for lang in LANGUAGES), key


def test_placeholders_match_across_languages():
    for key, entry in STRINGS.items():
        assert fields(entry["tr"]) == fields(entry["en"]) == fields(entry["de"]), key


def test_month_lists_have_twelve_entries():
    for lang in LANGUAGES:
        assert len(translate("months", lang).split(",")) == 12


def test_all_keys_used_in_source_exist():
    app = (SRC / "app.py").read_text(encoding="utf-8")
    used = set(re.findall(r"""\bt\(\s*["']([a-z0-9_]+)["']""", app))
    # Keys built from internal codes, e.g. t(f"country_{c}")
    from config import COUNTRY_MAP

    used |= {f"country_{c}" for c in COUNTRY_MAP}
    used |= {f"{prefix}_{p}" for prefix in ("timeframe", "per") for p in ("Monthly", "Quarterly", "Annual")}
    used |= {"model_linear", "model_loglog"}
    used |= {f"pf_status_{s}" for s in ("ok", "no_optimum", "no_profit")}
    from config import FILE_FORMATS

    used |= {f"file_format_{f}" for f in FILE_FORMATS}
    for module in ("data_ingestion.py", "optimizer.py"):
        used |= set(re.findall(r"""Msg\(\s*["']([a-z0-9_]+)["']""", (SRC / module).read_text(encoding="utf-8")))
    assert used, "regex found no keys"
    assert used - set(STRINGS) == set()


def test_dynamic_keys_cover_config():
    from config import COUNTRY_MAP, PERIOD_MULT

    for c in COUNTRY_MAP:
        assert f"country_{c}" in STRINGS
    for p in PERIOD_MULT:
        assert f"timeframe_{p}" in STRINGS and f"per_{p}" in STRINGS
    from config import FILE_FORMATS

    for f in FILE_FORMATS:
        assert f"file_format_{f}" in STRINGS


def test_msg_is_english_string_and_localizes():
    m = Msg("warn_rows_dropped", dropped=3, n_raw=5)
    assert isinstance(m, str)
    assert m.startswith("3 of 5 rows dropped")
    assert localize(m, "tr").startswith("5 satırdan 3 tanesi")
    assert localize(m, "de").startswith("3 von 5 Zeilen")


def test_msg_format_specs():
    m = Msg("warn_extrapolated", p_min=1234.5, p_max=2000)
    assert "(1,234.50–2,000.00)" in m


def test_msg_survives_pickle():
    m = Msg("warn_cost_filled", n=4)
    back = pickle.loads(pickle.dumps(m))
    assert back == m and back.key == "warn_cost_filled" and back.params == {"n": 4}
    assert localize(back, "de") == translate("warn_cost_filled", "de", n=4)


def test_localize_passes_plain_strings_through():
    assert localize("plain text", "tr") == "plain text"
    assert localize(ValueError("boom"), "de") == "boom"


@pytest.mark.parametrize("lang", ["fr", ""])
def test_translate_falls_back_to_english(lang):
    assert translate("app_title", lang) == "Pricing Optimization Engine"


def test_translate_unknown_key_returns_key():
    assert translate("no_such_key", "tr") == "no_such_key"


def test_keys_built_at_runtime_exist():
    from optimizer import SENSITIVITY_FACTORS

    keys = {f"sens_factor_{f}" for f in SENSITIVITY_FACTORS} | {"sens_low", "sens_high", "model_auto"}
    keys |= {f"badge_conf_{c}" for c in ("high", "medium", "low")}
    assert keys - set(STRINGS) == set()


def test_numbers_and_money_follow_the_language():
    from translations import fmt_money, fmt_number

    assert fmt_number(1234567.891, ",.2f", "en") == "1,234,567.89"
    assert fmt_number(1234567.891, ",.2f", "tr") == fmt_number(1234567.891, ",.2f", "de") == "1.234.567,89"
    assert fmt_money(593913.14, "₺", "tr") == "593.913,14 ₺"
    assert fmt_money(49492.76, "R$", "en") == "R$49,492.76"
    assert fmt_money(-12.5, "€", "de") == "-12,50 €"
    assert fmt_money(-0.001, "$", "en") == "$0.00"  # rounds to zero: no minus sign
    for sym in ("$", "€", "£", "₺", "R$"):
        assert fmt_money(1000, sym, "en").startswith(sym) and fmt_money(1000, sym, "tr").endswith(" " + sym)


def test_message_numbers_use_the_language_separators():
    assert "(1.234,50–56.789,00)" in translate("warn_extrapolated", "de", p_min=1234.5, p_max=56789.0)
    assert "(1,234.50–56,789.00)" in translate("warn_extrapolated", "en", p_min=1234.5, p_max=56789.0)
    assert "%90,0" in translate("warn_fees_exceed_price", "tr", fees=90.0, net=83.3)
    assert "Yalnızca 2 aylık" in translate("err_too_few_months", "tr", n=2, min_n=3)  # plain ints unchanged
