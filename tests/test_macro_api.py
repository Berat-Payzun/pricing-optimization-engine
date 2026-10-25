import pandas as pd
import pytest

import macro_api
from macro_api import BROWSER_HEADERS, fx_from_series, get_fx, get_inflation, parse_fred_csv, parse_ons_months, yoy_inflation

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
