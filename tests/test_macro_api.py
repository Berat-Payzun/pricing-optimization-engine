import pandas as pd
import pytest

import macro_api
from macro_api import (BROWSER_HEADERS, fx_from_series, get_fx, get_inflation, parse_fred_csv, parse_oecd_csv,
                       parse_ons_months, rate_to_index, yoy_inflation)

FRED_CSV = """observation_date,CPIAUCSL
2024-01-01,100.0
2024-02-01,.
2024-03-01,102.0
2025-01-01,105.0
2025-03-01,107.1
"""


def test_parse_fred_csv_skips_missing_dots():
    s = parse_fred_csv(FRED_CSV)
    assert len(s) == 4
    assert s.index[0] == pd.Timestamp("2024-01-01")


def test_yoy_inflation():
    s = parse_fred_csv(FRED_CSV)
    assert yoy_inflation(s) == pytest.approx(5.0)  # 107.1 / 102.0


def test_parse_ons_months():
    s = parse_ons_months([{"date": "2026 AUG", "value": "143.6"}, {"date": "2026 SEP", "value": "144.1"}])
    assert s.index[-1] == pd.Timestamp("2026-09-01")
    assert s.iloc[-1] == 144.1


def test_fx_inversion_and_change():
    idx = pd.to_datetime(["2025-01-01", "2026-01-02"])
    rate, change, as_of = fx_from_series(pd.Series([1.25, 1.0], index=idx), invert=True)  # USD per GBP
    assert rate == pytest.approx(1.0)
    assert change == pytest.approx(25.0)  # 0.8 -> 1.0 local per USD = local currency weakened
    assert as_of == "2026-01-02"


class FakeResp:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def test_fred_request_sends_browser_user_agent(monkeypatch):
    captured = {}

    def fake_get(url, params=None, headers=None, **kw):
        captured["headers"] = headers
        return FakeResp(FRED_CSV)

    import curl_cffi.requests as cffi_requests
    monkeypatch.setattr(cffi_requests, "get", fake_get)
    macro_api.fetch_fred_series("CPIAUCSL")
    assert captured["headers"]["User-Agent"].startswith("Mozilla/5.0")
    assert captured["headers"] is BROWSER_HEADERS


def test_inflation_falls_back_when_network_down(monkeypatch):
    def boom(*a, **kw):
        raise ConnectionError("offline")

    monkeypatch.setattr(macro_api, "http_get", boom)
    v = get_inflation("TR")
    assert not v.ok and v.source == "fallback default" and v.value > 0


def test_fx_falls_back_when_network_down(monkeypatch):
    def boom(*a, **kw):
        raise ConnectionError("offline")

    monkeypatch.setattr(macro_api, "http_get", boom)
    monkeypatch.setattr(macro_api, "fetch_yahoo_fx", boom)
    v = get_fx("GB")
    assert not v.ok and v.value > 0


def test_usd_needs_no_fx_fetch():
    v = get_fx("US")
    assert v.ok and v.value == 1.0 and v.change_pct == 0.0


OECD_CSV = """STRUCTURE,STRUCTURE_ID,REF_AREA,TIME_PERIOD,OBS_VALUE
DATAFLOW,X,BRA,2026-09,178.5
DATAFLOW,X,BRA,2025-09,170.0
DATAFLOW,X,BRA,2026-08,177.1
"""


def test_parse_oecd_csv_sorts_by_date():
    s = parse_oecd_csv(OECD_CSV)
    assert list(s.index) == list(pd.to_datetime(["2025-09-01", "2026-08-01", "2026-09-01"]))
    assert yoy_inflation(s) == pytest.approx(5.0)  # 178.5 / 170.0


WORLD_CSV = """observation_date,FPCPITOTLZGWLD
2022-01-01,8.0
2023-01-01,5.0
2024-01-01,3.0
2025-01-01,4.0
"""


def test_rate_to_index_is_monthly_and_keeps_annual_rates():
    idx = rate_to_index(parse_fred_csv(WORLD_CSV))
    assert idx.index[0] == pd.Timestamp("2022-07-01") and idx.index[-1] == pd.Timestamp("2025-07-01")
    assert len(idx) == 37 and idx.index.freqstr == "MS"
    assert yoy_inflation(idx) == pytest.approx(4.0)
    assert idx[pd.Timestamp("2024-07-01")] / idx[pd.Timestamp("2023-07-01")] == pytest.approx(1.03)
    # Log-linear in between: six months is half the year's growth
    assert idx[pd.Timestamp("2025-01-01")] / idx[pd.Timestamp("2024-07-01")] == pytest.approx(1.04 ** (184 / 365), rel=1e-4)


def test_world_inflation_from_annual_rates(monkeypatch):
    monkeypatch.setattr(macro_api, "http_get", lambda *a, **kw: FakeResp(WORLD_CSV))
    v = get_inflation("WORLD")
    assert v.ok and v.value == pytest.approx(4.0)
    assert v.as_of == "2025" and v.source == "FRED FPCPITOTLZGWLD"


def test_brazil_uses_oecd_first(monkeypatch):
    monkeypatch.setattr(macro_api, "http_get", lambda *a, **kw: FakeResp(OECD_CSV))
    v = get_inflation("BR")
    assert v.ok and v.source.startswith("OECD") and v.as_of == "2026-09"


@pytest.mark.parametrize("country", ["WORLD", "BR", "DE"])
def test_new_countries_fall_back_offline(monkeypatch, country):
    def boom(*a, **kw):
        raise ConnectionError("offline")

    monkeypatch.setattr(macro_api, "http_get", boom)
    monkeypatch.setattr(macro_api, "fetch_yahoo_fx", boom)
    assert not get_inflation(country).ok
    fx = get_fx(country)
    assert fx.value > 0 and (fx.ok if country == "WORLD" else not fx.ok)


def test_world_is_priced_in_usd():
    v = get_fx("WORLD")
    assert v.ok and v.value == 1.0 and v.change_pct == 0.0


def test_every_country_is_fully_configured():
    from config import COUNTRY_MAP, FALLBACK_MACRO

    assert set(FALLBACK_MACRO) == set(COUNTRY_MAP)
    for code, cfg in COUNTRY_MAP.items():
        assert cfg["cpi_sources"], code
        assert all(provider in macro_api.CPI_FETCHERS for provider, _ in cfg["cpi_sources"]), code


def test_euro_countries_share_eurozone_fx_but_not_its_cpi():
    from config import COUNTRY_MAP

    eu = COUNTRY_MAP["EU"]
    for code in ("DE", "FR", "IT", "ES"):
        cfg = COUNTRY_MAP[code]
        assert (cfg["currency"], cfg["fx_yahoo"], cfg["fx_fred"], cfg["fx_invert"]) == (
            eu["currency"], eu["fx_yahoo"], eu["fx_fred"], eu["fx_invert"])
        assert cfg["cpi_sources"][0] != eu["cpi_sources"][0]
