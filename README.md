# Pricing Optimization Engine

A Streamlit app that finds the **profit-maximizing price** for a product from its sales history and stress-tests it against **live macroeconomic data**: CPI inflation and exchange rates for the selected country.

Upload a CSV of past prices and quantities. The engine fits a demand curve, sweeps 2,000 candidate prices, and charts revenue, cost and net profit against price. Sliders let you simulate inflation, currency and competitor shocks and see how the optimal price and profit move.

![screenshot placeholder](docs/screenshot.png)

## Features

- **Demand estimation:** linear OLS or log-log (constant elasticity) regression, with R² shown for both so you can pick the better fit.
- **Competitor-aware (optional):** if the CSV has competitor prices, the model estimates the cross-price effect (XED) and enables a competitor-shock slider.
- **Inflation-adjusted history:** historical prices are deflated with the country's CPI before fitting. Without this, in high-inflation economies like Turkey, nominal price rises would be mistaken for real ones.
- **Live macro data:**
  - CPI from FRED (or the ONS for the UK)
  - FX from Yahoo Finance, with FRED as the fallback
  - Results cached for 6 hours. If a source is offline, the app falls back to built-in defaults and shows a badge.
- **Shock simulation:** inflation (raises COGS and fixed costs), FX shift (raises only the imported share of COGS), competitor price change.
- **Operational limits:** capacity/inventory ceiling and fixed costs; results shown per month, quarter or year.

## Quick start

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

The app opens with `sample_data.csv` loaded. You can regenerate it with `python scripts/generate_sample_data.py`; its true demand is `Q/day = 120 − 2·P + 1·P_comp`. Run the tests with `pytest`.

## CSV schema

| Column | Type | Required | Notes |
|---|---|---|---|
| `Date` | YYYY-MM-DD | yes | Daily, weekly or monthly rows; aggregated to months |
| `Price_Charged` | float | yes | Local currency of the selected country |
| `Quantity_Sold` | int | yes | |
| `Cost_Per_Unit` | float | no | Missing values use the sidebar "Default COGS" |
| `Competitor_Price` | float | no | Enables cross-price elasticity and the competitor slider |

Column names are matched case-insensitively, and common aliases (`price`, `qty`, `cost`, `competitor`) are accepted.

## Supported countries and data sources

| Country | CPI series | FX (local per USD) |
|---|---|---|
| United States | FRED `CPIAUCSL` | 1.0 (base currency) |
| Eurozone (euro-area average) | FRED `CP0000EZ19M086NEST` (Eurostat HICP) | Yahoo `EURUSD=X` (inverted); fallback FRED `DEXUSEU` |
| Germany | FRED `CP0000DEM086NEST` (Eurostat HICP); fallback `DEUCPIALLMINMEI` | as Eurozone |
| France | FRED `CP0000FRM086NEST` (Eurostat HICP); fallback `FRACPIALLMINMEI` | as Eurozone |
| Italy | FRED `CP0000ITM086NEST` (Eurostat HICP); fallback `ITACPIALLMINMEI` | as Eurozone |
| Spain | FRED `CP0000ESM086NEST` (Eurostat HICP); fallback `ESPCPIALLMINMEI` | as Eurozone |
| United Kingdom | ONS CPI index `D7BT`; fallback FRED `GBRCPIALLMINMEI` | Yahoo `GBPUSD=X` (inverted); fallback FRED `DEXUSUK` |
| Turkey | FRED `CP0000TRM086NEST` (Eurostat HICP); fallback `TURCPIALLMINMEI` | Yahoo `TRY=X` |
| Brazil | OECD SDMX `BRA.M.N.CPI.IX._T.N._Z`; fallback FRED `BRACPIALLMINMEI` | Yahoo `BRL=X`; fallback FRED `DEXBZUS` |
| Global (World) | FRED `FPCPITOTLZGWLD` (World Bank, annual % rate) | 1.0 (priced in USD) |

**Notes**
- The OECD MEI monthly CPI series (`…CPIALLMINMEI`) stopped updating in 2025, so they are only fallbacks. Eurostat HICP, ONS and the OECD's live SDMX API are used first.
- Eurozone is the euro-area average. Pick a specific country for its own inflation; all euro countries share the same EUR/USD rate.
- The global series is an annual inflation rate. It is converted to a monthly index (each year centred on 1 July, log-linear in between). Because it lags by about a year, the most recent months are not inflation-adjusted, and the app says so in the data notes.
- FRED blocks plain Python HTTP clients, so requests go through `curl_cffi` with browser impersonation and a browser User-Agent.
- No API keys are needed.

To add a country, add an entry to `COUNTRY_MAP` and `FALLBACK_MACRO` in `src/config.py`.

## The math

| Step | What happens |
|---|---|
| 1. Aggregation | Raw rows → calendar months (quantity summed, price quantity-weighted). Results are scaled ×1/×3/×12 for the chosen timeframe. |
| 2. Demand fit | Linear: `Q = a + b·P (+ c·P_comp)`. Log-log: `ln Q = a + b·ln P (+ c·ln P_comp)`. Fitted on real (CPI-deflated) prices. Log-log drops zero-sales months and flags them in the UI. |
| 3. Elasticities | PED = `b·P/Q` (linear) or `b` (log-log); XED = `c·P_comp/Q` or `c`. |
| 4. Competitor shock | Demand is re-predicted at `P_comp × (1 + shift)`. |
| 5. Capacity cap | `Q_sold = min(Q_demand × period_mult, capacity)` |
| 6. FX shock | `COGS_fx = COGS × (1 + import_share × fx_shift)` |
| 7. Inflation | `COGS_final = COGS_fx × (1 + π)`, `Fixed_final = Fixed_monthly × (1 + π) × period_mult` |
| 8. Optimization | Profit = `(P − COGS_final) × Q_sold − Fixed_final`, evaluated on a 2,000-point grid from just below unit cost to the max test price. The argmax is the optimal price P*. |

For linear demand without a capacity cap, the result matches the closed-form optimum `P* = (a + c·P_comp − b·COGS) / (−2b)` (verified in the tests).

**Assumptions and limits**
- Prices and the fitted demand are in *today's money*. The inflation slider projects costs forward but assumes customers' willingness to pay doesn't change.
- Demand is estimated from your own price history, so if prices barely varied, or price changes coincided with promotions or seasonality, the estimate can be biased. The app warns when demand slopes upward or when P* is outside the observed price range.
- One product per file.

## Project structure

```
├── sample_data.csv
├── scripts/generate_sample_data.py
├── src/
│   ├── app.py              # Streamlit UI
│   ├── config.py           # country → series mapping, defaults
│   ├── data_ingestion.py   # CSV cleaning, monthly aggregation, CPI deflation
│   ├── macro_api.py        # FRED / ONS / Yahoo fetchers with fallback
│   └── optimizer.py        # demand fit, elasticities, shock pipeline, solver
└── tests/
```
