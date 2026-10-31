# Pricing Optimization Engine

[![tests](https://github.com/Berat-Payzun/pricing-optimization-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/Berat-Payzun/pricing-optimization-engine/actions/workflows/tests.yml)

A Streamlit app that finds the **profit-maximizing price** for a product from its sales history and stress-tests it against **live macroeconomic data**: CPI inflation and exchange rates for the selected country.

Upload a CSV or Excel file of past prices and quantities. The engine fits a demand curve, sweeps 2,000 candidate prices, and charts revenue, cost and net profit against price. The headline is a **recommended price for today**: today's costs and price level, after VAT and channel fees, within your guardrails. Separately, sliders simulate the next 12 months of inflation, currency and competitor shocks.

## Features

- **Demand estimation:** linear OLS or log-log (constant elasticity) regression. **Auto** (the default) picks the model with the lower backtest error, or the higher R² when there is too little data for a backtest, and says which one it chose.
- **Backtest:** each of the last 6 months is forecast by a model fitted only on the months before it, at the price actually charged. The headline card shows this out-of-sample error (WAPE) against a naive "same as last month" forecast, for both models, instead of the in-sample R², which flatters the fit. R² is still listed in the model details, next to an actual-vs-forecast chart.
- **Seasonality (optional):** month-of-year effects in the demand fit, so a seasonal peak isn't mistaken for low price sensitivity. On by default with 24+ months of data.
- **Growth trend (optional):** a linear time trend in the demand fit, so steady growth or decline isn't mistaken for a price effect. With real prices under high inflation the real price falls month after month, so without it growth makes demand look more price-sensitive than it is. Demand is then priced at the latest month's level.
- **Today's recommendation vs the 12-month scenario:** the headline price uses today's costs and price level, with no shock. The macro scenario has its own cards and chart below the sliders, in the money of 12 months after the last sales month, so a forecast of inflation is never mistaken for a price rise to make today.
- **Fees & taxes:** one **variable selling costs %** for everything charged as a share of the price, such as marketplace commission, card/payment fee or sales and distributor commission (charged on the customer-facing price, including VAT), a "prices include VAT" toggle with the country's standard rate prefilled (TR 20%, DE/Eurozone 19%, FR 20%, IT 22%, ES 21%, UK 20%, US/Brazil/Global 0%), and an extra per-unit cost for shipping or packaging. A **unit economics & tax breakdown** shows where each unit's price goes.
- **Guardrails:** max change from the current price (±15% by default), minimum margin per unit, price floor and ceiling, and rounding to x.99, x.90 or whole numbers. When a rule binds, the unconstrained optimum and the limiting rule are shown next to the recommendation.
- **Price test plan:** a controlled test that checks the demand estimate. It alternates the current and a test price week by week, so seasons and trends affect both alike. You choose the test price step (10% by default); the app shows the weeks needed for that step, given your sales' normal week-to-week variation, and a chart of how a bigger step shortens the test. The plan lists expected weekly units with 90% bands. Type in actual weekly units and the app says whether customers react as the model expects, or are more or less price-sensitive. The plan is in the Excel export with an empty Actual column.
- **Uncertainty range:** a bootstrap (200 refits on resampled months) gives a 90% range for the optimal price, shown under the metric and as a band on the chart when no guardrail binds.
- **Elasticity confidence:** the same bootstrap gives a 90% confidence interval for the price elasticity at the recommended price, with a high / medium / low confidence badge (from the interval's width relative to its centre; low whenever the interval includes zero).
- **Sensitivity (tornado chart):** "What moves the optimal price?" re-runs today's optimization with each input moved ±10% (unit cost, price sensitivity, variable selling costs, VAT, exchange rate, competitor price; inflation by ±10 percentage points) and ranks them by how far the optimal price moves. Also in the Excel export.
- **Competitor-aware (optional):** if the CSV has competitor prices, the model estimates the cross-price effect (XED) and enables a competitor-shock slider.
- **Competitor reaction:** two sliders set how much of your price cuts and of your rises the competitor copies (both 0% by default, the optimistic case). The reaction feeds the recommendation, the scenario and the 90% range, and the headline shows what the price would be without a reaction. The weekly price test keeps the competitor fixed.
- **Inflation-adjusted history:** historical prices are deflated with the country's CPI before fitting. Without this, in high-inflation economies like Turkey, nominal price rises would be mistaken for real ones.
- **Live macro data:**
  - CPI from the official FRED API (or the ONS for the UK, the OECD for Brazil)
  - FX from Yahoo Finance, with FRED as the fallback
  - Results cached for 6 hours. If a source is offline, the app falls back to built-in defaults and shows a badge.
- **Shock simulation:**
  - inflation raises fixed costs and the locally sourced share of COGS
  - an FX shift (plus US inflation) raises the imported, USD-priced share of COGS
  - competitor price change
  - a "customer prices rise with inflation" toggle decides whether inflation also lifts willingness to pay and the competitor's price
- **Operational limits:** capacity/inventory ceiling and fixed costs; results shown per month, quarter or year.
- **Unit cost override:** test "what if my unit cost were X?" without editing the file.
- **Several products per file:** add a `Product` column and pick the product in the sidebar. An **All products** table recommends today's price for every product at once (model, change, elasticity, contribution gain, backtest error, or the reason a product can't be priced), with the shared fees, VAT and guardrails. Gains are contribution before fixed costs, which aren't split by product. Also in the Excel export.
- **Duplicate rows:** exact duplicate rows (common when overlapping exports are combined) are removed with a warning. Turn the option off for transaction logs where identical sales are real.
- **Export:** download an Excel workbook (summary, today's profit curve, scenario curve, monthly data, models) or a PDF summary with the main chart. Text in the workbook is always stored as text, so a product name like `=HYPERLINK(...)` from an uploaded file can't become a live formula.
- **Saved scenarios:** "Save scenario" in the sidebar downloads every setting, plus any actual units typed into a running price test, as a small JSON file. "Load scenario" restores it later. The file never contains your sales data, only a fingerprint of it, so the app warns when you load a scenario against a different sales file. Files stay on your computer: Streamlit Cloud's server disk is wiped on restart and shared by all visitors. Loading only parses JSON and checks every value (unknown settings skipped, out-of-range numbers clipped).
- **Three languages:** English, Turkish and German, switchable from the sidebar without losing inputs.

## Quick start

Requires Python 3.12 or newer.

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

`requirements.txt` pins exact versions. To upgrade, bump a version, run `pytest`, then commit.

### FRED API key

Most inflation data comes from FRED, which needs a free API key:

1. Create an account at https://fredaccount.stlouisfed.org/ and request a key at https://fredaccount.stlouisfed.org/apikeys.
2. **Locally:** create `.streamlit/secrets.toml` (already in `.gitignore`) with one line, `FRED_API_KEY = "your-key"`. An environment variable `FRED_API_KEY` works too.
3. **Streamlit Community Cloud:** open the app's ⋮ menu, then **Settings → Secrets**, and paste the same line.

Without a key the app still runs: FRED series fall back to built-in values, and a data note says so. The tests never use a real key.

### Deploying updates

Streamlit Community Cloud pulls every push to `main` and reloads `app.py`, but modules it imports (`optimizer.py`, `macro_api.py`, …) can stay loaded in their old version. A change that touches both can then fail with errors like `TypeError: ScenarioParams.__init__() got an unexpected keyword argument`. After merging such a change, open **Manage app → ⋮ → Reboot app**.

The app opens with `sample_data.csv` loaded: four products with known demand curves, each showing a different feature. Regenerate it with `python scripts/generate_sample_data.py`.

| Product | History | True demand | Try |
|---|---|---|---|
| Classic Mug | 24 months | `Q/day = 120 − 2·P + 1·P_comp`, weekend promos flagged | The default view; Auto picks linear |
| Travel Mug | 24 months | Constant elasticity −1.8, demand growing 2% a month, no competitor prices | Turn on the growth trend: Auto switches to log-log and the backtest error drops |
| Gift Set | 36 months | `Q/day = (60 − 0.8·P + 0.4·P_comp) × season` (Nov/Dec peak), December stockouts flagged | Turn on seasonality: the backtest error drops |
| New Tumbler | 2 months | Just launched | Too few months to price: the **All products** table shows why |

Run the tests with `pytest`.

## File format (CSV or Excel)

| Column | Type | Required | Turkish / German names also accepted | Notes |
|---|---|---|---|---|
| `Date` | YYYY-MM-DD | yes | Tarih / Datum | Daily, weekly or monthly rows; aggregated to months |
| `Price_Charged` | float | yes | Fiyat, Satış Fiyatı / Preis, Verkaufspreis | Local currency of the selected country |
| `Quantity_Sold` | int | yes | Adet, Miktar / Menge, Absatz, Stück | |
| `Cost_Per_Unit` | float | no | Maliyet, Birim Maliyet / Kosten, Stückkosten | Missing values use the sidebar "Default COGS" |
| `Competitor_Price` | float | no | Rakip Fiyatı / Konkurrenzpreis | Enables cross-price elasticity and the competitor slider |
| `Product` | text | no | Ürün / Produkt, Artikel (also `SKU`) | Several products in one file; pick one in the sidebar |
| `Flag` | text | no | Durum / Kennzeichen, Hinweis (also `Status`) | `stockout` or `promo` (also `stok yok`, `kampanya` / `ausverkauft`, `Aktion`). Flagged days are left out of the demand fit (see below) |

Column names are matched case-insensitively, ignoring accents, spaces and dashes. English aliases (`price`, `qty`, `cost`, `competitor`) work too.

**Stockouts and promotions.** Sales on a stockout day understate demand, and promo days sell at a temporary price, so both would bias the demand curve. Days with a flagged row are left out: a month's sales come from its clean days, scaled up to all its days (`Q × days / clean days`). A month where more than half the days are flagged is shown in the charts but left out of the fit, and a promo month is never used as the "current" price.

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
- FRED is read through its official API (`api.stlouisfed.org`) with your key (see Quick start). The key is sent only to FRED and is never shown in errors or logs. ONS and OECD need no key.
- This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.

To add a country, add an entry to `COUNTRY_MAP` and `FALLBACK_MACRO` in `src/config.py`.

## The math

| Step | What happens |
|---|---|
| 1. Aggregation | Raw rows → calendar months (quantity summed, price quantity-weighted). Results are scaled ×1/×3/×12 for the chosen timeframe. |
| 2. Demand fit | Linear: `Q = a + b·P (+ c·P_comp)`. Log-log: `ln Q = a + b·ln P (+ c·ln P_comp)`. Fitted on real (CPI-deflated) prices. Log-log drops zero-sales months and flags them in the UI. With seasonality on, 11 month dummies are added (January as base). The effects are re-centred to average zero, so the optimizer prices for a typical month. With the growth trend on, a month counter `g·t` is added and the intercept is set to the last month's level (the 12-month scenario does not project the trend forward). |
| 3. Elasticities | PED = `b·P/Q` (linear) or `b` (log-log); XED = `c·P_comp/Q` or `c`. |
| 4. Competitor shock and reaction | Demand is re-predicted at `P_comp × (1 + shift)`. With a reaction, at each candidate price the competitor also copies part of your real price move from today's price: `P_comp × (1 + shift) × (1 + m × (P_real / P_current − 1))`, where `m` is the cut share for cuts and the rise share for rises. Matching rises makes demand look less price-sensitive (your relative price barely moves), so keep the guardrails on when you use it. |
| 5. Capacity cap | `Q_sold = min(Q_demand × period_mult, capacity)` |
| 6. FX shock | The imported share follows the exchange rate and US inflation: `share × (1 + fx_shift) × (1 + π_USD)`. `π_USD` has its own slider, prefilled with the latest US CPI; for USD countries it equals the inflation slider. |
| 7. Inflation | The rest follows local inflation: `COGS_final = COGS × [share × (1 + fx_shift)(1 + π_USD) + (1 − share)(1 + π)] + Extra × (1 + π)`, `Fixed_final = Fixed_monthly × (1 + π) × period_mult` |
| 8. Optimization | Profit = `(P / (1 + VAT) − f × P − COGS_final) × Q_sold − Fixed_final`, where f is the variable selling costs rate,, evaluated on a 2,000-point grid from just below unit cost to the max test price. The argmax is the optimal price P*. With price pass-through on, demand is evaluated at the real price `P / (1 + π)` and the competitor's price rises by `(1 + π)`. |

| 9. Guardrails | Today's optimum is restricted to `current × (1 ± max change)`, the floor/ceiling and the minimum margin `(P/(1+VAT) − fees − COGS) / (P/(1+VAT))`, then rounded to the better of the price points below and above with the chosen ending. If the floor or ceiling lies outside the max-change band, max change is ignored; if no price in the band reaches the minimum margin, the margin rule is dropped. Both cases are flagged. The 12-month scenario is not restricted. |

For linear demand without a capacity cap, the result matches the closed-form optimum `P* = (a + c·P_comp)/(−2b) + COGS/(2k)` with `k = 1/(1 + VAT) − f` (`k = 1` without VAT or fees; verified in the tests).

**Backtest.** For each of the last 6 fitted months (fewer, down to 3, when early windows are too short), the model is refitted on the earlier months only and predicts that month's sales at its actual price, competitor price and month. Error is WAPE = Σ|actual − forecast| / Σ actual. The naive benchmark predicts each month's sales as the previous month's. Windows shorter than 24 months fit without seasonality, as the app would have at the time.

**Price test plan.** The test price is `current × (1 ± step)`, in the direction of the unconstrained optimum, kept within the guardrails (with a warning when they hold it back) and rounded to the price ending. The step is set in the app (default 10%). Weekly expected units are the model's monthly prediction for an average month × 12/52, capped by capacity. Weekly noise is `max(in-sample residual SD, backtest RMSE) / √(52/12)`. Weeks per price are `n = ⌈2·(1.645 + 0.84)²·σ²/D²⌉` (90% confidence, 80% power for the expected weekly difference `D`), with 4–24 weeks in total and a warning when 24 weeks aren't enough. Because `D` grows with the step while `σ` does not, the weeks needed fall roughly with the square of the step: doubling it cuts the test to about a quarter. The verdict compares the observed difference between the two prices' mean weekly sales, with a 90% interval, to the expected `D`.

**90% range.** The months are resampled with replacement 200 times. The demand model is refitted each time and today's P* recomputed (with the same fees, before guardrails). The 5th–95th percentiles form the range.

**Assumptions and limits**
- The demand curve is fitted in *today's money*.
  - With "customer prices rise with inflation" on (the default), the inflation slider lifts the whole price level: costs, willingness to pay and the competitor's price. The optimal price then keeps pace with inflation.
  - With it off, only costs rise. This shows the margin squeeze if you can't pass costs on.
  - Shocked prices and profits are in the scenario's (inflated) money.
- Demand is estimated from your own price history. If prices barely varied, or price changes coincided with promotions, the estimate can be biased (the seasonality option handles recurring monthly patterns). The app warns when demand slopes upward or when P* is outside the observed price range, and the 90% range shows how firmly the data pins down P*.
- Each product is modelled on its own. Effects between your own products, such as cannibalisation, are not modelled.

## Project structure

```
├── .github/workflows/tests.yml   # runs pytest with coverage on every push and pull request
├── assets/fonts/          # DejaVu Sans for the PDF export (covers Turkish letters and ₺)
├── sample_data.csv
├── scripts/generate_sample_data.py
├── src/
│   ├── app.py              # Streamlit UI
│   ├── config.py           # country → series mapping, defaults
│   ├── data_ingestion.py   # CSV/Excel reading, header aliases, monthly aggregation, CPI deflation
│   ├── macro_api.py        # FRED / ONS / OECD / Yahoo fetchers with fallback
│   ├── optimizer.py        # demand fit (seasonality, trend), elasticities, shock pipeline, solver, bootstrap, sensitivity
│   ├── portfolio.py        # today's recommendation for every product in a file
│   ├── report.py           # Excel and PDF export
│   ├── scenarios.py        # save / load scenarios as JSON
│   └── translations.py     # UI strings in English, Turkish and German
└── tests/                  # unit tests per module, plus test_app.py: the whole app run headless (network stubbed)
```
