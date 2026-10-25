# Plan: Pricing Optimization Engine (Streamlit MVP)

## Context
The repo `C:\Projects\pricing-optimization-engine` is empty apart from `.git`, and the machine has Python 3.15. The app will let a company upload its sales history (price, quantity, unit cost, optional competitor price) and pick a country. It then:
1. fits a demand curve
2. finds the profit-maximizing price
3. charts price against revenue, cost and profit
4. lets the user stress-test the result with inflation, FX and competitor shock sliders. Defaults come from live FRED and Yahoo Finance data.

The plan follows the user's architecture guide, with these corrections and the choices the user confirmed:
- **Competitor price is optional.** When it's present, fit one regression with both prices, Q = a + b·P + c·P_comp, and get XED from it. When it's absent, disable the competitor slider and show a note explaining why.
- **No `pandas_datareader`.** It's unmaintained and breaks on Python ≥3.12. Get CPI from FRED's keyless CSV endpoint `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>`. Get FX from `yfinance`, falling back to FRED `DEX*`. Yahoo has no CPI series, so FRED is the only CPI source.
- **Period consistency fix.** The guide multiplies fixed costs for the whole history by Period_Factor while using revenue for a single period. Instead, everything is computed for the period the user picks: data is aggregated by month, and results are scaled ×1, ×3 or ×12 for Monthly, Quarterly or Annual.
- **FX exposure:** a "% of COGS priced in USD" input. Only that share of unit cost moves with the FX shift.
- **Demand model:** linear OLS by default, with a log-log (constant elasticity) toggle. R² is shown for both.
- **Inflation:** CPI deflates historical prices to real terms before fitting. The inflation slider also raises COGS and fixed costs.
- **One product per file.**

## Structure
```
pricing-optimization-engine/
├── .gitignore  README.md  requirements.txt  sample_data.csv
├── scripts/generate_sample_data.py     # reproducible synthetic data with known elasticity
├── src/
│   ├── app.py            # Streamlit UI
│   ├── config.py         # COUNTRY_MAP + defaults
│   ├── data_ingestion.py # CSV load/validate/clean/aggregate/deflate
│   ├── macro_api.py      # FRED + Yahoo fetchers with caching & fallback
│   └── optimizer.py      # demand fit, elasticities, shock pipeline, solver
└── tests/  test_data_ingestion.py  test_optimizer.py  test_macro_api.py
```
`requirements.txt`: pandas, numpy, scikit-learn (or plain `numpy.linalg.lstsq`, which avoids an extra dependency; I'll use sklearn as the guide asks), streamlit, plotly, yfinance, requests, pytest.

## Modules

### `config.py`: country mapping
`COUNTRY_MAP = {code: {name, currency, symbol, cpi_fred, fx_yahoo, fx_fred, fx_invert}}`
- US: `CPIAUCSL`, FX fixed at 1.0, `$`
- TR: CPI `TURCPIALLMINMEI` (OECD MEI). Check during implementation that it's still updated. If it's stale, use the World Bank annual series `FPCPITOTLZGTUR` and show the data's as-of date. FX: `TRY=X` (USD/TRY), fallback `DEXTKUS`. Symbol `₺`.
- EU/DE: `CP0000EZ19M086NEST`, `EURUSD=X` (invert so it reads as local per USD), `DEXUSEU`. Symbol `€`.
- GB: `GBRCPIALLMINMEI`, `GBPUSD=X` (invert), `DEXUSUK`. Symbol `£`.

### `macro_api.py`
- `fetch_fred_series(series_id, start) -> pd.Series`: requests + `pd.read_csv` on fredgraph.csv, with a timeout. Sends a standard desktop-browser `User-Agent` header (a module constant `BROWSER_HEADERS`) so FRED doesn't block the request with a 403. Also handles FRED's "." missing values. A test asserts the header is sent.
- `get_inflation(country) -> MacroValue(value_pct, as_of, source, ok)`: year-over-year % from the latest CPI value against the value 12 months earlier, plus the full CPI series used for deflating.
- `get_fx(country) -> MacroValue`: latest local-per-USD rate and its 12-month % change, from yfinance with FRED as fallback.
- Wrapped in `@st.cache_data(ttl=6h)` inside app.py, not in this module, so the module stays testable. Every failure returns `ok=False` with hard-coded fallback defaults, and the UI shows an "offline / manual" badge instead of crashing.

### `data_ingestion.py`
- `load_csv(file) -> (df, warnings)`: normalizes column names. Requires `Date`, `Price_Charged`, `Quantity_Sold`. `Cost_Per_Unit` and `Competitor_Price` are optional.
- Validation: parse dates; coerce numerics; drop rows with price ≤0 or quantity <0; fill missing cost with the UI default COGS; forward-fill gaps in competitor price; report dropped row counts.
- `aggregate(df, freq="MS")`: total quantity per period, average price weighted by quantity, mean cost and mean competitor price. Fewer than 6 periods triggers a warning, and below 3 the fit is blocked.
- `deflate(agg, cpi_series)`: align CPI by month, rebase to the latest month, then `real_price = price × CPI_latest / CPI_t` (same for competitor price). If CPI isn't available, use nominal prices and show a warning.

### `optimizer.py`: the 8-step pipeline as pure functions
1. **Aggregate and normalize to periods:** done in ingestion. `PERIOD_MULT = {Monthly:1, Quarterly:3, Annual:12}`.
2. **Demand fit** `fit_demand(agg, model="linear"|"loglog") -> DemandModel(a, b, c|None, r2, n, n_dropped, model, price_range)`. `n_dropped` counts the periods excluded from a log-log fit (Q≤0 or Pc≤0).
   - linear: Q = a + b·P (+ c·Pc). `predict(P, Pc) = max(0, …)`.
   - log-log: ln Q = a + b·ln P (+ c·ln Pc). Prediction is `exp(...)`.
   - Warn if b ≥ 0, i.e. demand slopes upward, which means the data can't identify the curve. Rows with Q=0 are skipped in log-log.
3. **Elasticities:**
   - PED: linear b·P/Q(P), log-log b.
   - XED: linear c·Pc/Q, log-log c. Both are evaluated at the current price and at P*.
4. **Competitor shock:** shift Pc by s_c% and predict directly with the new Pc. This is more exact than the guide's Q·(1+XED·s) approximation and gives the same result to first order.
5. **Capacity cap:** `Q_sold = min(Q_pred, capacity / PERIOD_MULT…)`. Capacity is entered for the selected period. A marker shows where the cap binds.
6. **FX on COGS:** `COGS_fx = COGS × (1 + import_share × fx_shift%)`
7. **Inflation:**
   - `COGS_final = COGS_fx × (1+π)`
   - `Fixed_final = Fixed_monthly × (1+π) × PERIOD_MULT`
8. **Solver:** `optimize(model, params) -> Result`. It builds a price grid of 2,000 points from max(COGS_final, 0.01) to `max_price` (default 2× the highest historical real price; the user can change it). It computes revenue, variable cost, total cost and profit on the grid (all scaled by PERIOD_MULT) and takes the argmax for P*. The grid scales with price level, which avoids the guide's fixed $0.10 step that is too coarse for TRY prices and slow for large ranges.
   - The result also includes: baseline metrics at the current/last price, uplift vs baseline, break-even prices (profit=0 crossings), and a flag when P* falls outside the historically observed price range (an extrapolation warning).
   - `run_scenario(...)` combines steps 4–8 so the UI and tests call a single entry point.

### `app.py`: Streamlit layout
- **Sidebar:**
  - CSV upload, plus a "Use sample data" button
  - country selector
  - default COGS
  - monthly fixed costs
  - capacity per period
  - timeframe
  - imported COGS share %
  - demand model toggle
  - max price
- **Top metric cards:** optimal price (with Δ vs current), peak net profit (with Δ), PED at P*, R², CPI YoY %, FX rate (with source and as-of date badge).
- **Charts (Plotly):**
  1. Main chart: revenue, total cost and net profit against price on the left axis, with demand quantity on a secondary axis. Vertical lines mark P* and the current price; capacity-binding and break-even regions are shaded.
  2. Price history with competitor price over time; also nominal vs real if CPI is available.
  3. Scenario comparison: baseline (no shock) vs shocked profit curve overlaid, so the shock's impact is visible.
- **Shock sliders** (below the charts, as the guide specifies): inflation %, FX shift %, competitor price change %. Defaults come from the fetched values (CPI YoY, 12-month FX change), and a "Reset to live data" button restores them.
- **Log-log drop badge:** when the log-log model is active and `n_dropped > 0`, a warning badge appears next to the R² card, e.g. "⚠ 3 of 24 periods dropped (zero sales) for log-log fit". The same note goes into the warnings expander.
- Expander showing the fitted coefficients, the equation and the data-quality warnings.

### `sample_data.csv`
Generated by `scripts/generate_sample_data.py`: 24 months of daily rows with linear demand plus noise, a known slope and competitor effect, a slowly drifting cost and a competitor price series. This lets tests check that the fit recovers the true parameters.

## Verification
1. `pip install -r requirements.txt`, then `pytest`. The tests cover:
   - ingestion: missing columns, NaNs, cost fallback, aggregation
   - optimizer: recovers the synthetic slope within tolerance; analytic linear P* = (a + c·Pc + b·COGS)/(−2b) matches the grid argmax; the capacity cap moves P* up; FX and inflation shocks move P* in the expected direction; log-log fit recovers known elasticity
   - macro_api: FRED CSV parsing with a mocked response; fallback when the network fails
2. Live check: run `fetch_fred_series` and `get_fx` for all 4 countries and print the latest values and as-of dates. Confirm the Turkey CPI series isn't stale and change the mapping if it is.
3. `streamlit run src/app.py`: load the sample data, check each country, move each slider and confirm the charts and metrics update. Also confirm the app still works with the network disconnected (fallback badge).
4. Write the README: setup, CSV schema, the math (8 steps plus the deviations above), screenshots placeholder.
5. Make a single initial commit only if the user asks.

## Build Checklist
- [x] Project scaffolding (`.gitignore`, `requirements.txt`, folder layout)
- [x] `src/config.py` — country mapping (live series verified)
- [x] `src/macro_api.py` — FRED (browser User-Agent) + Yahoo fetchers with fallback
- [x] `src/data_ingestion.py` — load / validate / aggregate / deflate
- [x] `src/optimizer.py` — demand fit (linear + log-log), elasticities, 8-step shock pipeline, 2,000-point solver
- [x] `scripts/generate_sample_data.py` + `sample_data.csv`
- [x] `src/app.py` — Streamlit dashboard (metrics, charts, shock sliders, log-log drop badge)
- [x] Tests (`tests/`) passing
- [x] Live macro data check for all 4 countries
- [x] App smoke-run (`streamlit run src/app.py`)
- [x] `README.md`

## Changes made during the build
- **FRED access:** a browser User-Agent alone still got blocked (FRED fingerprints the TLS handshake), so requests use `curl_cffi` with Chrome impersonation plus `BROWSER_HEADERS`; plain `requests` is the fallback.
- **CPI sources (verified live 2026-10-25):** Turkey and UK OECD MEI series stopped updating in 2025.
  - Turkey uses Eurostat HICP `CP0000TRM086NEST`.
  - UK uses the ONS CPI index `D7BT`.
  - The stale series are kept as fallbacks.
- **Turkey FX:** FRED `DEXTKUS` doesn't exist (404), so TRY uses Yahoo `TRY=X` only.
- **Charts:** no dual-axis chart. The profit/revenue/cost curve and the demand (quantity) curve are separate charts, and the demand chart overlays the observed monthly points.
- **Formula fix:** the analytic linear optimum is `P* = (a + c·Pc − b·COGS)/(−2b)`; the plan had a sign error on the COGS term.
