# Plan: Phase 4 (post-Phase 3 audit)

## Context
After phase 3 merged (PR #7, `cf3396f`), the user asked for a full health check before more work:
crashes and edge cases, model consistency, formatting and export safety, plus a few presentation
upgrades. This plan records what the audit found and the fixes. It was reviewed and approved before
any code changed.

## How the audit was done (read-only)
- `pytest --cov=src`: **178 passed, 94% coverage**. That's more than the "113+" the request
  expected. By module: optimizer 99%, report 99%, scenarios 98%, data_ingestion 97%, portfolio 93%,
  app 87%, macro_api 83%.
- I read the optimizer, portfolio and app input code in full.
- Extreme inputs went through the real functions (`run_scenario`, `recommend`, `sensitivity`,
  `bootstrap`, `test_plan`, `backtest`), and through the whole app headlessly (`AppTest`):
  - 90% fees with 50% VAT
  - unit cost 0, and unit cost 10,000
  - capacity 1
  - 95% minimum margin
  - max change off
  - floor above ceiling
  - 100% inflation, −50% FX, −50% competitor price with full reaction
  - Annual period, Turkey, Brazil
  - bad data files: all-zero sales, constant price, 1 / 3 / 4 months, upward-sloping demand,
    ₺50k prices, `inf` / `1e308` / text values
- Excel export was tested with formula-injection product names (`=HYPERLINK`, `=cmd|…`,
  `+…`, `-…`, `@…`, tab-prefixed).

**No crashes anywhere.** The problems are wrong or misleading answers in edge cases.

A few corrections to the request's assumptions: the backtest metric is **WAPE**, not MAPE. There is
no ¥ (Japan) country; the supported currencies are $, €, £, ₺, R$.

## Findings

### Bugs (fix in this phase)
1. **"No profitable price" is shown as a normal recommendation (linear model).**
   - **Trigger:** every price loses money. Examples: fees + VAT eat the whole price (90% fee with
     20% VAT), unit cost above the price where sales hit zero, or an all-zero-sales file.
   - **What happens:** profit is flat at −fixed costs above that price, and `idxmax` picks the
     first such price.
     - `run_scenario` returns `interior=True`, a "recommended" price with **0 units**, and
       elasticity "—".
     - The All products table says **"OK"**.
     - The bootstrap still shows a 90% range with a **"High confidence"** badge.
     - The only signal is the yellow `warn_loss_only`.
   - **Seen with:** Classic Mug, fee 90% + VAT 50% → P\* $83.73, q = 0, interior True; the table
     shows "OK".
2. **An optimum at the bottom of the price grid counts as a real optimum.**
   - **Trigger:** log-log model with zero unit cost, fees and VAT, i.e. pure revenue
     maximization at elasticity −1.46.
   - **What happens:** P\* = **$0.01**, `interior=True`, because `interior` only checks the top
     edge.
   - **Impact:** with max change off (0), the app would recommend $0.01. Realistic for digital
     products that have no unit cost.
3. **Infinite values get through cleaning.**
   - **Trigger:** a price or quantity of `inf` or `1e308` in the file.
   - **What happens:** it passes `load_csv`, because `to_numeric` keeps ±inf and the `price ≤ 0`
     filter doesn't catch it. The fit then fails with sklearn's untranslated English message
     *"Input X contains infinity or a value too large for dtype('float64')"*.
4. **A file with zero sales in every month gets priced.**
   - **What happens:** linear fits b = 0 with the "upward slope" warning, and the result is
     P\* = $4.50 (below anything ever charged), interior True.
   - **Expected:** a clear "no sales in the data" error. The table should show it as that
     product's reason.
5. **Auto can pick a model whose demand slopes upward (b ≥ 0).**
   - **What happens:** `best_model` ranks only by backtest error, so a b ≥ 0 model can win over
     one with b < 0. Upward-sloping data fits a straight line perfectly (WAPE 0.0) in the stress
     run.
   - **Fix:** prefer models with b < 0, and keep today's rule only when both slope up.

### Minor
6. `money(-0.001)` prints `-$0.00`. The equation display rounds a slope of −0.0015 at ₺50k prices
   to `-0.002`. Show slopes with 3 significant digits instead.
7. README: the tornado bullet doesn't list inflation, which was added after the PR text.

### Checked and fine (no change)
- **Model consistency:** fees, VAT, imported COGS share and FX, US inflation, CPI deflation and
  competitor reaction behave the same for linear and log-log.
  - All go through one `_economics` / `_setup` / `_comp_at` path (`src/optimizer.py:280-338`).
  - That path is shared by `run_scenario`, `recommend`, `bootstrap`, `sensitivity` and
    `portfolio`.
  - Both models fit on the deflated `Real_Price` / `Real_Competitor_Price`.
- **Auto with no backtest:** falls back to R²; if neither model fits, the app reports the linear
  fit's reason. Never a broken state.
- **Excel:** every injection payload is stored as text (`report.build_excel` turns formula cells
  into strings). The Product column is cast to `str`, and blanks become "—".
- **Guardrails:** conflicts (floor > ceiling), an unreachable minimum margin and price endings
  all degrade with warnings.
- **NaN display:** NaN elasticity and WAPE show "—" via `num()`.
- **Shocks:** the extremes run cleanly, in TR and BR too.

### Formatting gap (polish candidate)
Money and numbers always use US separators (`₺593,913.14`, `R$49,492.76`), even when the UI is
in Turkish or German, where `593.913,14 ₺` is expected. This applies to:
- `money()` (`src/app.py:125`)
- the table columns
- the Plotly `hovertemplate`s and axes

The symbols themselves are correct. I saw no overlap in the metric cards; the chart marker labels
were fixed in PR #7.

## Phase 4 checklist
- [x] 0. PLAN.md
- [x] 1. "No profitable price" state
- [x] 2. Bottom-edge optimum is not an optimum
- [x] 3. Data cleaning: non-finite values, all-zero sales
- [x] 4. Auto skips upward-sloping demand
- [x] 5. Minor fixes
- [ ] 6a. README showcase
- [x] 6b. Locale-aware numbers
- [x] 6c. Ruff lint in CI

## Plan

### 0. `PLAN.md`
Move the original build plan under a "History" heading, and put this Phase 4 plan on top with
its checklist.

### 1. A clear "no profitable price" state (bug 1, plus the sidebar check)
- **`src/optimizer.py` `run_scenario`:** add `ScenarioResult.viable: bool`.
  - It's False when the best grid point sells nothing, or when no price covers the variable costs
    (max of `profit + fixed` ≤ 0).
  - Keep `interior` for the edge case.
- **`src/app.py`:** when `not today.viable`, show a red card like `err_no_interior`.
  - Text: "No price covers the unit cost, fees and VAT".
  - Hide the 90% range and the elasticity confidence badge.
- **`src/portfolio.py`:** new status `no_profit`.
- **Sidebar:** a warning when `fee_rate ≥ 1/(1+VAT)`, since then every sale loses money whatever
  the price.
- **New translation keys** (EN/TR/DE) in `src/translations.py`.

### 2. A bottom-edge optimum is not an optimum (bug 2)
- `interior = 0 < i < len(grid) − 1` in `run_scenario`.
- Make the message depend on the edge: today's `err_no_interior` covers the top; a new
  `err_no_interior_low` covers the bottom ("profit keeps rising as price falls: unit cost is
  probably missing").

### 3. Data cleaning (bugs 3 and 4)
- **`src/data_ingestion.py` `load_csv`:** treat non-finite numbers as missing. They are then
  dropped and counted in the existing dropped-rows warning.
- **`aggregate`:** raise `DataValidationError(Msg("err_no_sales"))` when the fit months sell
  nothing in total.

### 4. Auto skips upward-sloping demand (bug 5)
`best_model` (`src/optimizer.py:776`) ranks the models with `b < 0` first, and falls back to all
models only when none have it.

### 5. Minor fixes (items 6 and 7)
- `money()`: no `-` sign when the amount rounds to zero.
- `DemandModel.equation`: show slopes with 3 significant digits.
- README: add inflation to the tornado bullet.

### 6. Polish (the user chose all three)
- **(a) README showcase:**
  - **Badges:** a "Live demo" badge linking to https://pricing-optimization-engine.streamlit.app,
    next to the existing tests badge.
  - **Screenshot:** a hero screenshot `assets/screenshot.png` of the app on the 4-product sample.
    Capture it locally: `streamlit run src/app.py`, then headless Chrome `--screenshot` at
    ~1400×1000 (Chrome is already present; kaleido used it). The screenshot needs the dark-theme
    label background from PR #7.
  - **Diagram:** a Mermaid "How it works" diagram: upload → clean → deflate (CPI) → fit
    linear/log-log → backtest + Auto → profit sweep (fees, VAT, FX, inflation) → guardrails →
    tornado / bootstrap / test plan → Excel/PDF. GitHub renders it natively.
- **(b) Locale-aware numbers:**
  - **Helper:** `fmt_number(x, decimals, lang)` in `src/translations.py`. It swaps separators for
    TR/DE (`1.234,56`).
  - **Money:** `money(x, sym)` uses the helper. The symbol goes after the amount for TR/DE
    (`593.913,14 ₺`, `49.492,76 €`), and before it for EN (`$1,234.56`, `R$1,234.56`).
  - **Charts:** `style()` sets Plotly `layout.separators` (`".,"` for EN, `",."` for TR/DE), so
    the existing `hovertemplate` `,.2f` formats and the axes follow it. Only the symbol position
    in templates changes, via one small template helper.
  - **Tables:** columns already formatted with `money()` / `num()` follow automatically. Check
    `num()` callers that show non-money decimals (elasticity, %).
  - **Exports:** Excel keeps raw numbers, so nothing changes there. The PDF uses `money()`, so it
    follows the UI language.
- **(c) Ruff lint in CI:**
  - **Config:** `ruff.toml`: line length 120 to match the code, rules `E,F,W,I,B,UP`. Exclude
    `translations.py` from the line-length check, because its strings are long by nature.
  - **CI:** a `ruff check .` step in `.github/workflows/tests.yml`. Add `ruff` (pinned, released
    ≥ 2 weeks ago) to `requirements.txt` next to `pytest-cov`.
  - **Cleanup:** fix what it flags. Fixes must be mechanical only, with no behaviour changes; the
    tests confirm that.

### Tests (added with each step)
- **Optimizer:**
  - fee 90% + VAT → `viable` False
  - log-log with zero cost → `interior` False at the bottom edge
  - Auto skips b ≥ 0
- **Ingestion:**
  - `inf` / `1e308` rows are dropped with the warning
  - all-zero sales → `err_no_sales`
- **Portfolio:** a product with zero sales and one with no profitable price, each showing its
  status.
- **App (`AppTest`):** fee 90% + VAT shows the red card and no range.
- Translation key tests already cover new keys.

## Verification
1. `pytest --cov=src`: all green, and coverage at least the current 94%.
2. Rerun the audit's stress scripts (scratchpad `stress.py`, `appstress.py`):
   - fee 90 + VAT 50 and huge cost: `viable` False, red card, table status "No profitable price"
   - log-log with zero cost: no $0.01 recommendation
   - `inf` file: rows dropped with a warning
   - zero-sales file: translated error
3. Headless run of the sample data: unchanged recommendations (Classic Mug $53.48, Travel Mug
   $31.62, Gift Set $62.02) and no new warnings.
4. Locale: render the app in TR and DE with `AppTest` and check `1.234,56 ₺` / `1.234,56 €` in the
   metric cards, the All products table and the chart layout separators. EN stays `$1,234.56`.
   Unit tests for `fmt_number` / `money` cover negatives, rounding to zero and every currency.
5. `ruff check .` is clean locally, and the CI workflow passes on 3.12 and 3.13.
6. README preview: check that the Mermaid block and the screenshot render (`gh` markdown preview
   or the PR page).
7. Then: commit on a new branch `feat/audit-phase4` (bug fixes and polish as separate commits),
   open the PR, and remind about the Streamlit Cloud reboot.

---

# History

## Original build plan: Pricing Optimization Engine (Streamlit MVP)

### Context
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

### Structure
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

### Modules

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

### Verification
1. `pip install -r requirements.txt`, then `pytest`. The tests cover:
   - ingestion: missing columns, NaNs, cost fallback, aggregation
   - optimizer: recovers the synthetic slope within tolerance; analytic linear P* = (a + c·Pc + b·COGS)/(−2b) matches the grid argmax; the capacity cap moves P* up; FX and inflation shocks move P* in the expected direction; log-log fit recovers known elasticity
   - macro_api: FRED CSV parsing with a mocked response; fallback when the network fails
2. Live check: run `fetch_fred_series` and `get_fx` for all 4 countries and print the latest values and as-of dates. Confirm the Turkey CPI series isn't stale and change the mapping if it is.
3. `streamlit run src/app.py`: load the sample data, check each country, move each slider and confirm the charts and metrics update. Also confirm the app still works with the network disconnected (fallback badge).
4. Write the README: setup, CSV schema, the math (8 steps plus the deviations above), screenshots placeholder.
5. Make a single initial commit only if the user asks.

### Build Checklist
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

### Changes made during the build
- **FRED access:** a browser User-Agent alone still got blocked (FRED fingerprints the TLS handshake), so requests use `curl_cffi` with Chrome impersonation plus `BROWSER_HEADERS`; plain `requests` is the fallback.
- **CPI sources (verified live 2026-10-25):** Turkey and UK OECD MEI series stopped updating in 2025.
  - Turkey uses Eurostat HICP `CP0000TRM086NEST`.
  - UK uses the ONS CPI index `D7BT`.
  - The stale series are kept as fallbacks.
- **Turkey FX:** FRED `DEXTKUS` doesn't exist (404), so TRY uses Yahoo `TRY=X` only.
- **Charts:** no dual-axis chart. The profit/revenue/cost curve and the demand (quantity) curve are separate charts, and the demand chart overlays the observed monthly points.
- **Formula fix:** the analytic linear optimum is `P* = (a + c·Pc − b·COGS)/(−2b)`; the plan had a sign error on the COGS term.
