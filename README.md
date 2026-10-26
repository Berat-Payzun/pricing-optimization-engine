# Pricing Optimization Engine

[![tests](https://github.com/Berat-Payzun/pricing-optimization-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/Berat-Payzun/pricing-optimization-engine/actions/workflows/tests.yml)

A Streamlit app that finds the **profit-maximizing price** for a product from its sales history and stress-tests it against **live macroeconomic data**: CPI inflation and exchange rates for the selected country.

Upload a CSV or Excel file of past prices and quantities. The engine fits a demand curve, sweeps 2,000 candidate prices, and charts revenue, cost and net profit against price. Sliders let you simulate inflation, currency and competitor shocks and see how the optimal price and profit move.

## Features

- **Demand estimation:** linear OLS or log-log (constant elasticity) regression, with R² shown for both so you can pick the better fit.
- **Seasonality (optional):** month-of-year effects in the demand fit, so a seasonal peak isn't mistaken for low price sensitivity. On by default with 24+ months of data.
- **Uncertainty range:** a bootstrap (200 refits on resampled months) gives a 90% range for the optimal price, shown under the metric and as a band on the chart.
- **Competitor-aware (optional):** if the CSV has competitor prices, the model estimates the cross-price effect (XED) and enables a competitor-shock slider.
- **Inflation-adjusted history:** historical prices are deflated with the country's CPI before fitting. Without this, in high-inflation economies like Turkey, nominal price rises would be mistaken for real ones.
- **Live macro data:**
  - CPI from FRED (or the ONS for the UK)
  - FX from Yahoo Finance, with FRED as the fallback
  - Results cached for 6 hours. If a source is offline, the app falls back to built-in defaults and shows a badge.
- **Shock simulation:**
  - inflation raises fixed costs and the locally sourced share of COGS
  - an FX shift (plus US inflation) raises the imported, USD-priced share of COGS
  - competitor price change
  - a "customer prices rise with inflation" toggle decides whether inflation also lifts willingness to pay and the competitor's price
- **Operational limits:** capacity/inventory ceiling and fixed costs; results shown per month, quarter or year.
- **Unit cost override:** test "what if my unit cost were X?" without editing the file.
- **Several products per file:** add a `Product` column and pick the product in the sidebar.
- **Export:** download an Excel workbook (summary, profit curve, monthly data, models) or a one-page PDF summary with the main chart.
- **Three languages:** English, Turkish and German, switchable from the sidebar without losing inputs.

## Quick start

Requires Python 3.12 or newer.

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

`requirements.txt` pins exact versions. To upgrade, bump a version, run `pytest`, then commit.

The app opens with `sample_data.csv` loaded. You can regenerate it with `python scripts/generate_sample_data.py`; its true demand is `Q/day = 120 − 2·P + 1·P_comp`. Run the tests with `pytest`.

## File format (CSV or Excel)

| Column | Type | Required | Turkish / German names also accepted | Notes |
|---|---|---|---|---|
| `Date` | YYYY-MM-DD | yes | Tarih / Datum | Daily, weekly or monthly rows; aggregated to months |
| `Price_Charged` | float | yes | Fiyat, Satış Fiyatı / Preis, Verkaufspreis | Local currency of the selected country |
| `Quantity_Sold` | int | yes | Adet, Miktar / Menge, Absatz, Stück | |
| `Cost_Per_Unit` | float | no | Maliyet, Birim Maliyet / Kosten, Stückkosten | Missing values use the sidebar "Default COGS" |
| `Competitor_Price` | float | no | Rakip Fiyatı / Konkurrenzpreis | Enables cross-price elasticity and the competitor slider |
| `Product` | text | no | Ürün / Produkt, Artikel (also `SKU`) | Several products in one file; pick one in the sidebar |

Column names are matched case-insensitively, ignoring accents, spaces and dashes. English aliases (`price`, `qty`, `cost`, `competitor`) work too.

`.xlsx` files are read from the first sheet. CSVs saved by Excel in Turkish or German locales also work: `;` separators, decimal commas (`1.234,56`), `dd.mm.yyyy` dates and Windows encodings (cp1254/cp1252) are detected automatically.

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
| 2. Demand fit | Linear: `Q = a + b·P (+ c·P_comp)`. Log-log: `ln Q = a + b·ln P (+ c·ln P_comp)`. Fitted on real (CPI-deflated) prices. Log-log drops zero-sales months and flags them in the UI. With seasonality on, 11 month dummies are added (January as base). The effects are re-centred to average zero, so the optimizer prices for a typical month. |
| 3. Elasticities | PED = `b·P/Q` (linear) or `b` (log-log); XED = `c·P_comp/Q` or `c`. |
| 4. Competitor shock | Demand is re-predicted at `P_comp × (1 + shift)`. |
| 5. Capacity cap | `Q_sold = min(Q_demand × period_mult, capacity)` |
| 6. FX shock | The imported share follows the exchange rate and US inflation: `share × (1 + fx_shift) × (1 + π_USD)` |
| 7. Inflation | The rest follows local inflation: `COGS_final = COGS × [share × (1 + fx_shift)(1 + π_USD) + (1 − share)(1 + π)]`, `Fixed_final = Fixed_monthly × (1 + π) × period_mult` |
| 8. Optimization | Profit = `(P − COGS_final) × Q_sold − Fixed_final`, evaluated on a 2,000-point grid from just below unit cost to the max test price. The argmax is the optimal price P*. With price pass-through on, demand is evaluated at the real price `P / (1 + π)` and the competitor's price rises by `(1 + π)`. |

For linear demand without a capacity cap, the result matches the closed-form optimum `P* = (a + c·P_comp − b·COGS) / (−2b)` (verified in the tests).

**90% range.** The months are resampled with replacement 200 times. The demand model is refitted each time and P* recomputed under the same scenario. The 5th–95th percentiles form the range.

**Assumptions and limits**
- The demand curve is fitted in *today's money*.
  - With "customer prices rise with inflation" on (the default), the inflation slider lifts the whole price level: costs, willingness to pay and the competitor's price. The optimal price then keeps pace with inflation.
  - With it off, only costs rise. This shows the margin squeeze if you can't pass costs on.
  - Shocked prices and profits are in the scenario's (inflated) money.
- Demand is estimated from your own price history. If prices barely varied, or price changes coincided with promotions, the estimate can be biased (the seasonality option handles recurring monthly patterns). The app warns when demand slopes upward or when P* is outside the observed price range, and the 90% range shows how firmly the data pins down P*.
- Each product is modelled on its own. Effects between your own products, such as cannibalisation, are not modelled.

## Project structure

```
├── .github/workflows/tests.yml   # runs pytest on every push and pull request
├── assets/fonts/          # DejaVu Sans for the PDF export (covers Turkish letters and ₺)
├── sample_data.csv
├── scripts/generate_sample_data.py
├── src/
│   ├── app.py              # Streamlit UI
│   ├── config.py           # country → series mapping, defaults
│   ├── data_ingestion.py   # CSV/Excel reading, header aliases, monthly aggregation, CPI deflation
│   ├── macro_api.py        # FRED / ONS / OECD / Yahoo fetchers with fallback
│   ├── optimizer.py        # demand fit (incl. seasonality), elasticities, shock pipeline, solver, bootstrap
│   ├── report.py           # Excel and PDF export
│   └── translations.py     # UI strings in English, Turkish and German
└── tests/
```
