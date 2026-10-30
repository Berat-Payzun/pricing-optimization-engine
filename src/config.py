"""Country-to-API series mapping and app-wide defaults.

FX convention used everywhere in the app: rates are quoted as LOCAL CURRENCY PER 1 USD,
so a positive % change means the local currency weakened (imported inputs get pricier).
`fx_invert=True` marks tickers quoted the other way round (USD per local unit).

CPI sources are tried in order. Providers: "fred" and "oecd" return a monthly price index,
"ons" the UK ONS index, and "fred_rate" an ANNUAL % inflation rate that macro_api converts
to a monthly index. Series were verified live on 2026-10-26:
- OECD MEI monthly CPI series (xxxCPIALLMINMEI) stopped updating in 2025 (Germany, France,
  Italy, Spain, Turkey, UK: 2025-03; Brazil: 2025-04). EU countries and Turkey therefore use
  Eurostat's HICP (CP0000xxM086NEST), the UK the ONS CPI index (D7BT), and Brazil the OECD's
  live SDMX API, each with the stale MEI series kept as a fallback.
- "EU" is the euro-area average (HICP for the 19-country euro area), not any single country.
- FRED has no Turkish lira daily FX series (DEXTKUS returns 404), so TRY relies on Yahoo only.
- "vat" is the standard VAT rate (%) used as the default when prices include VAT. "EU" uses 19%
  as a euro-area placeholder; the US has state sales taxes added on top of the shelf price, and
  Brazil's layered taxes (ICMS, PIS/COFINS) don't fit one rate, so both start at 0.
- The World Bank's global inflation series on FRED is FPCPITOTLZGWLD (World = WLD); it is an
  annual % rate published with roughly a one-year lag.
"""

COUNTRY_MAP = {
    "US": {
        "name": "United States",
        "currency": "USD",
        "symbol": "$",
        "vat": 0,
        "cpi_sources": [("fred", "CPIAUCSL")],
        "fx_yahoo": None,
        "fx_fred": None,
        "fx_invert": False,
    },
    "EU": {
        "name": "Eurozone",
        "currency": "EUR",
        "symbol": "€",
        "vat": 19,
        "cpi_sources": [("fred", "CP0000EZ19M086NEST")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "DE": {
        "name": "Germany",
        "currency": "EUR",
        "symbol": "€",
        "vat": 19,
        "cpi_sources": [("fred", "CP0000DEM086NEST"), ("fred", "DEUCPIALLMINMEI")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "FR": {
        "name": "France",
        "currency": "EUR",
        "symbol": "€",
        "vat": 20,
        "cpi_sources": [("fred", "CP0000FRM086NEST"), ("fred", "FRACPIALLMINMEI")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "IT": {
        "name": "Italy",
        "currency": "EUR",
        "symbol": "€",
        "vat": 22,
        "cpi_sources": [("fred", "CP0000ITM086NEST"), ("fred", "ITACPIALLMINMEI")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "ES": {
        "name": "Spain",
        "currency": "EUR",
        "symbol": "€",
        "vat": 21,
        "cpi_sources": [("fred", "CP0000ESM086NEST"), ("fred", "ESPCPIALLMINMEI")],
        "fx_yahoo": "EURUSD=X",
        "fx_fred": "DEXUSEU",
        "fx_invert": True,
    },
    "GB": {
        "name": "United Kingdom",
        "currency": "GBP",
        "symbol": "£",
        "vat": 20,
        "cpi_sources": [("ons", "d7bt/mm23"), ("fred", "GBRCPIALLMINMEI")],
        "fx_yahoo": "GBPUSD=X",
        "fx_fred": "DEXUSUK",
        "fx_invert": True,
    },
    "TR": {
        "name": "Turkey",
        "currency": "TRY",
        "symbol": "₺",
        "vat": 20,
        "cpi_sources": [("fred", "CP0000TRM086NEST"), ("fred", "TURCPIALLMINMEI")],
        "fx_yahoo": "TRY=X",
        "fx_fred": None,
        "fx_invert": False,
    },
    "BR": {
        "name": "Brazil",
        "currency": "BRL",
        "symbol": "R$",
        "vat": 0,
        "cpi_sources": [("oecd", "BRA.M.N.CPI.IX._T.N._Z"), ("fred", "BRACPIALLMINMEI")],
        "fx_yahoo": "BRL=X",
        "fx_fred": "DEXBZUS",
        "fx_invert": False,
    },
    # No single global exchange rate: global goods are priced in the reserve currency (USD).
    "WORLD": {
        "name": "Global (World)",
        "currency": "USD",
        "symbol": "$",
        "vat": 0,
        "cpi_sources": [("fred_rate", "FPCPITOTLZGWLD")],
        "fx_yahoo": None,
        "fx_fred": None,
        "fx_invert": False,
    },
}

# Used when every live source fails, so the app still runs offline.
# Values: (annual inflation %, local-per-USD FX rate, 12-month FX change %), snapshot of 2026-10-26
FALLBACK_MACRO = {
    "US": (3.7, 1.0, 0.0),
    "EU": (3.75, 0.8912, 3.4),
    "DE": (3.26, 0.8912, 3.4),
    "FR": (3.42, 0.8912, 3.4),
    "IT": (4.17, 0.8912, 3.4),
    "ES": (4.96, 0.8912, 3.4),
    "GB": (3.45, 0.7477, -0.35),
    "TR": (29.7, 49.73, 18.5),
    "BR": (4.58, 5.05, -6.5),
    "WORLD": (3.04, 1.0, 0.0),
}

PERIOD_MULT = {"Monthly": 1, "Quarterly": 3, "Annual": 12}

PRICE_GRID_POINTS = 2000
MIN_PERIODS_WARN = 6
MIN_PERIODS_FIT = 3

# A CPI series ending more than this many months before the last sales month is flagged.
CPI_STALE_MONTHS = 3

# Month-of-year effects need two full years, or season and price can't be told apart.
SEASONAL_MIN_MONTHS = 24

# Resamples for the bootstrap range of the optimal price.
BOOTSTRAP_SAMPLES = 200

# Rolling backtest: forecast each of the last N months from the months before it.
BACKTEST_MONTHS = 6
BACKTEST_MIN_MONTHS = 3

# Price test plan: alternate the current and a test price week by week.
TEST_DEFAULT_STEP = 0.10  # test price = current price ± this, towards the optimum (user-adjustable)
TEST_STEP_CHOICES = (0.025, 0.05, 0.075, 0.10, 0.15, 0.20, 0.25, 0.30)  # shown in the step / duration trade-off
TEST_MIN_WEEKS, TEST_MAX_WEEKS = 4, 24

# Guardrail defaults: the largest price step recommended in one go
MAX_CHANGE_DEFAULT = 15.0  # %

DEFAULTS = {
    "cogs": 10.0,
    "fixed_costs": 5000.0,
    "capacity": 10000,
    "import_share": 30.0,
}
