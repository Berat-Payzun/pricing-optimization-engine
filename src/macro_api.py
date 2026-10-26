"""Country macro data fetcher: inflation (FRED / ONS / OECD) and FX rates (Yahoo Finance / FRED).

Every public function returns a MacroValue and never raises, so the UI can fall back
to manual inputs when a source is offline.

FRED's bot protection blocks plain Python HTTP clients based on their TLS fingerprint,
even with a browser User-Agent. Requests therefore go through `curl_cffi` (already a
yfinance dependency) impersonating Chrome, and send browser headers as well. Plain
`requests` with the same headers is the fallback.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import COUNTRY_MAP, FALLBACK_MACRO

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
ONS_URL = "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/{}/data"
OECD_URL = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/{}"
TIMEOUT = 20

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/json,text/html;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class MacroValue:
    value: float
    as_of: str | None
    source: str
    ok: bool
    change_pct: float | None = None  # FX only: 12-month % change
    series: pd.Series | None = field(default=None, repr=False)  # CPI only: full index


def http_get(url: str, params: dict | None = None):
    """GET with browser impersonation, falling back to plain requests."""
    try:
        from curl_cffi import requests as cffi_requests

        resp = cffi_requests.get(
            url, params=params, headers=BROWSER_HEADERS, impersonate="chrome", timeout=TIMEOUT
        )
    except Exception:
        import requests

        resp = requests.get(url, params=params, headers=BROWSER_HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp


def fetch_fred_series(series_id: str) -> pd.Series:
    resp = http_get(FRED_CSV_URL, params={"id": series_id})
    if not resp.text.startswith("observation_date") and not resp.text.startswith("DATE"):
        raise ValueError(f"FRED returned non-CSV content for {series_id}")
    return parse_fred_csv(resp.text)


def parse_fred_csv(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    s = pd.Series(
        pd.to_numeric(df.iloc[:, 1], errors="coerce").values,  # FRED marks gaps with "."
        index=pd.to_datetime(df.iloc[:, 0]),
        name=df.columns[1],
    )
    return s.dropna()


def fetch_ons_series(series_path: str) -> pd.Series:
    data = http_get(ONS_URL.format(series_path)).json()
    return parse_ons_months(data["months"])


def parse_ons_months(months: list[dict]) -> pd.Series:
    dates = pd.to_datetime([m["date"] for m in months], format="%Y %b")
    values = pd.to_numeric([m["value"] for m in months], errors="coerce")
    return pd.Series(values, index=dates, name="CPI").dropna()


def fetch_oecd_series(key: str) -> pd.Series:
    resp = http_get(OECD_URL.format(key), params={"startPeriod": "2000-01", "format": "csvfilewithlabels"})
    if not resp.text.startswith("STRUCTURE"):
        raise ValueError(f"OECD returned non-CSV content for {key}")
    return parse_oecd_csv(resp.text)


def parse_oecd_csv(text: str) -> pd.Series:
    df = pd.read_csv(io.StringIO(text))
    s = pd.Series(
        pd.to_numeric(df["OBS_VALUE"], errors="coerce").values,
        index=pd.to_datetime(df["TIME_PERIOD"]),
        name="CPI",
    )
    return s.sort_index().dropna()  # SDMX rows are not returned in date order


def rate_to_index(rates: pd.Series) -> pd.Series:
    """Turn annual % inflation rates into a monthly price index.

    Each year's rate is an annual average, so its index level is placed on 1 July and the
    months in between are interpolated log-linearly. deflate() then sees a smooth monthly
    index, and yoy_inflation() on the result returns the latest annual rate exactly.
    """
    rates = rates.sort_index()
    log_level = np.log1p(rates.values / 100).cumsum()
    annual = pd.Series(log_level, index=pd.to_datetime([f"{y}-07-01" for y in rates.index.year]))
    return np.exp(annual.resample("MS").asfreq().interpolate(method="time")).rename("CPI")


CPI_FETCHERS = {
    "fred": fetch_fred_series,
    "ons": fetch_ons_series,
    "oecd": fetch_oecd_series,
    "fred_rate": lambda series_id: rate_to_index(fetch_fred_series(series_id)),
}
ANNUAL_PROVIDERS = {"fred_rate"}


def yoy_inflation(cpi: pd.Series) -> float:
    """Year-over-year % change of the latest observation, robust to monthly or annual data."""
    latest_date = cpi.index[-1]
    prior = cpi[cpi.index <= latest_date - pd.DateOffset(months=12)]
    if prior.empty:
        raise ValueError("CPI series shorter than 12 months")
    return (cpi.iloc[-1] / prior.iloc[-1] - 1) * 100


def get_inflation(country: str) -> MacroValue:
    for provider, series_id in COUNTRY_MAP[country]["cpi_sources"]:
        try:
            cpi = CPI_FETCHERS[provider](series_id)
            annual = provider in ANNUAL_PROVIDERS
            return MacroValue(
                value=yoy_inflation(cpi),
                as_of=cpi.index[-1].strftime("%Y" if annual else "%Y-%m"),
                source=f"{provider.split('_')[0].upper()} {series_id}",
                ok=True,
                series=cpi,
            )
        except Exception:
            continue
    return MacroValue(FALLBACK_MACRO[country][0], None, "fallback default", ok=False)


def fx_from_series(rates: pd.Series, invert: bool) -> tuple[float, float, str]:
    rates = rates.dropna()
    if invert:
        rates = 1 / rates
    latest_date = rates.index[-1]
    prior = rates[rates.index <= latest_date - pd.DateOffset(months=12)]
    base = prior.iloc[-1] if not prior.empty else rates.iloc[0]
    return float(rates.iloc[-1]), float((rates.iloc[-1] / base - 1) * 100), latest_date.strftime("%Y-%m-%d")


def fetch_yahoo_fx(ticker: str) -> pd.Series:
    import warnings

    import yfinance as yf

    with warnings.catch_warnings():  # yfinance triggers pandas deprecation warnings on pandas 3.x
        warnings.simplefilter("ignore")
        hist = yf.Ticker(ticker).history(period="13mo", interval="1d")
    if hist.empty:
        raise ValueError(f"No Yahoo data for {ticker}")
    closes = hist["Close"]
    closes.index = closes.index.tz_localize(None)
    return closes


def get_fx(country: str) -> MacroValue:
    cfg = COUNTRY_MAP[country]
    if cfg["fx_yahoo"] is None and cfg["fx_fred"] is None:
        return MacroValue(1.0, None, "base currency", ok=True, change_pct=0.0)

    attempts = []
    if cfg["fx_yahoo"]:
        attempts.append((f"Yahoo {cfg['fx_yahoo']}", lambda: fetch_yahoo_fx(cfg["fx_yahoo"])))
    if cfg["fx_fred"]:
        attempts.append((f"FRED {cfg['fx_fred']}", lambda: fetch_fred_series(cfg["fx_fred"])))

    for source, fetch in attempts:
        try:
            rate, change, as_of = fx_from_series(fetch(), cfg["fx_invert"])
            return MacroValue(rate, as_of, source, ok=True, change_pct=change)
        except Exception:
            continue
    _, rate, change = FALLBACK_MACRO[country]
    return MacroValue(rate, None, "fallback default", ok=False, change_pct=change)
