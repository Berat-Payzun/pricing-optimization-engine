"""Country-to-API series mapping and app-wide defaults.

FX convention used everywhere in the app: rates are quoted as LOCAL CURRENCY PER 1 USD,
so a positive % change means the local currency weakened (imported inputs get pricier).
`fx_invert=True` marks tickers quoted the other way round (USD per local unit).

CPI sources are tried in order. Series were verified live on 2026-10-25:
- OECD MEI monthly CPI for Turkey (TURCPIALLMINMEI) and the UK (GBRCPIALLMINMEI) stopped
  updating in 2025, so Turkey uses Eurostat's HICP (CP0000TRM086NEST) and the UK uses
  the ONS CPI index (series D7BT), with the stale FRED series kept as a fallback.
- FRED has no Turkish lira daily FX series (DEXTKUS returns 404), so TRY relies on Yahoo only.
"""

COUNTRY_MAP = {
    "US": {
        "name": "United States",
        "currency": "USD",
        "symbol": "$",
        "cpi_sources": [("fred", "CPIAUCSL")],
        "fx_yahoo": None,
        "fx_fred": None,
        "fx_invert": False,
    },
    "TR": {
        "name": "Turkey",
        "currency": "TRY",
        "symbol": "₺",
        "cpi_sources": [("fred", "CP0000TRM086NEST"), ("fred", "TURCPIALLMINMEI")],
        "fx_yahoo": "TRY=X",
        "fx_fred": None,
        "fx_invert": False,
    },
    "EU": {
        "name": "Eurozone / Germany",
        "currency": "EUR",
        "symbol": "€",
        "cpi_sources": [("fred", "CP0000EZ19M086NEST")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "GB": {
        "name": "United Kingdom",
        "currency": "GBP",
        "symbol": "£",
        "cpi_sources": [("ons", "d7bt/mm23"), ("fred", "GBRCPIALLMINMEI")],
        "fx_yahoo": "GBPUSD=X",
        "fx_fred": "DEXUSUK",
        "fx_invert": True,
    },
}

# Used when every live source fails, so the app still runs offline.
# Values: (annual inflation %, local-per-USD FX rate, 12-month FX change %), snapshot of 2026-10-25
FALLBACK_MACRO = {
    "US": (3.7, 1.0, 0.0),
    "TR": (29.7, 49.73, 18.5),
    "EU": (3.75, 0.8925, 3.6),
    "GB": (3.45, 0.7477, -0.35),
}

PERIOD_MULT = {"Monthly": 1, "Quarterly": 3, "Annual": 12}

PRICE_GRID_POINTS = 2000
MIN_PERIODS_WARN = 6
MIN_PERIODS_FIT = 3

DEFAULTS = {
    "cogs": 10.0,
    "fixed_costs": 5000.0,
    "capacity": 10000,
    "import_share": 30.0,
}
