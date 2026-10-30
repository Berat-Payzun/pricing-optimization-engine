import numpy as np
import pandas as pd
import pytest

from optimizer import DemandModel, ScenarioParams, fit_demand, run_scenario, shocked_costs

A, B, C = 3000.0, -60.0, 30.0  # true monthly demand: Q = A + B*P + C*Pc


def synthetic_agg(kind="linear", n=36, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(30, 60, n)
    pc = rng.uniform(40, 55, n)
    if kind == "linear":
        q = A + B * p + C * pc
    else:  # constant elasticity -2.5, cross elasticity 0.8
        q = np.exp(10 - 2.5 * np.log(p) + 0.8 * np.log(pc))
    q = q * (1 + rng.normal(0, noise, n))
    idx = pd.date_range("2023-01-01", periods=n, freq="MS")
    return pd.DataFrame({"Price_Charged": p, "Competitor_Price": pc, "Quantity_Sold": q, "Cost_Per_Unit": 20.0}, index=idx)


def params(model, **kw):
    base = dict(base_cogs=20.0, fixed_monthly=1000.0, capacity=1e12, base_comp_price=50.0,
                current_price=45.0, max_price=120.0)
    base.update(kw)
    return ScenarioParams(**base)


def test_linear_fit_recovers_true_coefficients():
    m = fit_demand(synthetic_agg(noise=0.02), "linear")
    assert m.b == pytest.approx(B, rel=0.1)
    assert m.c == pytest.approx(C, rel=0.25)
    assert m.r2 > 0.9


def test_loglog_fit_recovers_elasticities():
    m = fit_demand(synthetic_agg("loglog", noise=0.02), "loglog")
    assert m.b == pytest.approx(-2.5, rel=0.05)
    assert m.c == pytest.approx(0.8, rel=0.15)
    assert m.n_dropped == 0


def test_loglog_drops_zero_sales_periods():
    agg = synthetic_agg("loglog")
    agg.iloc[[0, 5, 9], agg.columns.get_loc("Quantity_Sold")] = 0
    m = fit_demand(agg, "loglog")
    assert m.n_dropped == 3
    assert m.n == len(agg) - 3
    assert any("3 of 36 periods dropped" in w for w in m.warnings)


def test_grid_optimum_matches_analytic_linear_solution():
    m = fit_demand(synthetic_agg(), "linear")
    r = run_scenario(m, params(m))
    a_eff = m.intercept + m.c * 50.0
    analytic = (a_eff - m.b * 20.0) / (-2 * m.b)
    step = (r.curve["price"].iloc[1] - r.curve["price"].iloc[0])
    assert r.optimal["price"] == pytest.approx(analytic, abs=step)


def test_capacity_cap_raises_optimal_price():
    m = fit_demand(synthetic_agg(), "linear")
    free = run_scenario(m, params(m))
    capped = run_scenario(m, params(m, capacity=free.optimal["q_sold"] * 0.5))
    assert capped.optimal["price"] > free.optimal["price"]
    assert capped.optimal["q_sold"] <= free.optimal["q_sold"] * 0.5 + 1e-6


def test_period_scaling():
    m = fit_demand(synthetic_agg(), "linear")
    monthly = run_scenario(m, params(m))
    annual = run_scenario(m, params(m, period="Annual"))
    assert annual.optimal["price"] == pytest.approx(monthly.optimal["price"])
    assert annual.optimal["profit"] == pytest.approx(monthly.optimal["profit"] * 12, rel=1e-6)


def test_fx_hits_imported_share_and_local_inflation_the_rest():
    p = ScenarioParams(base_cogs=100, fixed_monthly=1000, capacity=1, import_share=0.4,
                       fx_shift=0.5, inflation=0.1, period="Quarterly")
    cogs, fixed = shocked_costs(p)
    assert cogs == pytest.approx(100 * (0.4 * 1.5 + 0.6 * 1.1))  # no local inflation on USD inputs
    assert fixed == pytest.approx(1000 * 1.1 * 3)


def test_imported_share_follows_usd_inflation():
    p = ScenarioParams(base_cogs=100, fixed_monthly=0, capacity=1, import_share=0.3,
                       fx_shift=0.185, inflation=0.297, usd_inflation=0.037)
    cogs, _ = shocked_costs(p)
    assert cogs == pytest.approx(100 * (0.3 * 1.185 * 1.037 + 0.7 * 1.297))


def test_passthrough_scales_linear_optimum_with_price_level():
    m = fit_demand(synthetic_agg(), "linear")
    base = run_scenario(m, params(m, max_price=200))
    infl = run_scenario(m, params(m, max_price=200, inflation=0.3, price_passthrough=True))
    # Costs, willingness to pay and the competitor all rise 30%, so P* rises 30% too
    assert infl.optimal["price"] == pytest.approx(base.optimal["price"] * 1.3, rel=2e-3)
    assert infl.comp_price == pytest.approx(50.0 * 1.3)
    assert infl.ped_opt == pytest.approx(base.ped_opt, rel=1e-2)
    # Same real economics, so no new warnings (e.g. no false "outside observed range")
    assert [w.key for w in infl.warnings] == [w.key for w in base.warnings]


def test_passthrough_off_only_raises_costs():
    m = fit_demand(synthetic_agg(), "linear")
    base = run_scenario(m, params(m))
    costs_only = run_scenario(m, params(m, inflation=0.3))
    assert base.optimal["price"] < costs_only.optimal["price"] < base.optimal["price"] * 1.3
    assert costs_only.comp_price == pytest.approx(50.0)


def test_passthrough_without_inflation_changes_nothing():
    m = fit_demand(synthetic_agg(), "linear")
    a = run_scenario(m, params(m))
    b = run_scenario(m, params(m, price_passthrough=True))
    assert a.optimal == b.optimal and a.baseline == b.baseline


def test_cost_shocks_raise_optimal_price_and_cut_profit():
    m = fit_demand(synthetic_agg(), "linear")
    base = run_scenario(m, params(m, import_share=0.5))
    shocked = run_scenario(m, params(m, import_share=0.5, fx_shift=0.3, inflation=0.2))
    assert shocked.optimal["price"] > base.optimal["price"]
    assert shocked.optimal["profit"] < base.optimal["profit"]


def test_competitor_price_rise_helps_us():
    m = fit_demand(synthetic_agg(), "linear")
    base = run_scenario(m, params(m))
    up = run_scenario(m, params(m, comp_shift=0.2))
    assert up.comp_price == pytest.approx(60.0)
    assert up.optimal["profit"] > base.optimal["profit"]


def test_no_competitor_data_model():
    agg = synthetic_agg().drop(columns="Competitor_Price")
    m = fit_demand(agg, "linear")
    assert not m.has_comp
    r = run_scenario(m, params(m, base_comp_price=None, comp_shift=0.5))
    assert r.comp_price is None and r.xed_opt is None


def test_upward_sloping_demand_warns():
    agg = synthetic_agg()
    agg["Quantity_Sold"] = 100 + 5 * agg["Price_Charged"]
    m = fit_demand(agg, "linear")
    assert any("slopes upward" in w for w in m.warnings)


def test_break_evens_bracket_the_optimum():
    m = fit_demand(synthetic_agg(), "linear")
    r = run_scenario(m, params(m, fixed_monthly=20000))
    assert len(r.break_evens) == 2
    lo, hi = r.break_evens
    assert lo < r.optimal["price"] < hi


def test_inelastic_loglog_hits_upper_bound_warning():
    m = DemandModel("loglog", 8.0, -0.5, None, 1.0, 10, 0, 30, 60)
    r = run_scenario(m, params(m, base_comp_price=None))
    assert r.optimal["price"] == pytest.approx(r.curve["price"].iloc[-1])
    assert any("top of the price search range" in w for w in r.warnings)


def seasonal_agg(n=36, seed=1):
    """Demand with a strong month-of-year pattern, and prices raised in the busy months,
    so a model without seasonality mistakes the seasonal peak for weak price sensitivity."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=n, freq="MS")
    season = 500 * np.sin(2 * np.pi * (idx.month.values - 1) / 12)
    p = 45 + 0.02 * season + rng.uniform(-6, 6, n)
    pc = rng.uniform(40, 55, n)
    q = A + B * p + C * pc + season
    return pd.DataFrame({"Price_Charged": p, "Competitor_Price": pc, "Quantity_Sold": q, "Cost_Per_Unit": 20.0}, index=idx)


def test_seasonal_fit_separates_season_from_price():
    agg = seasonal_agg()
    plain, seasonal = fit_demand(agg, "linear"), fit_demand(agg, "linear", seasonal=True)
    assert seasonal.b == pytest.approx(B, rel=0.02)
    assert abs(plain.b - B) > 0.1 * abs(B)  # biased without seasonality
    assert seasonal.r2 > plain.r2 and seasonal.r2 > 0.999
    assert seasonal.season is not None and seasonal.season.mean() == pytest.approx(0, abs=1e-9)
    # Effects recover the true pattern (true effects are mean zero over a full year)
    true = 500 * np.sin(2 * np.pi * np.arange(12) / 12)
    assert seasonal.season == pytest.approx(true, abs=1.0)
    assert seasonal.predict(45, 50, month=4) - seasonal.predict(45, 50) == pytest.approx(true[3], abs=1.0)
    assert "s(month)" in seasonal.equation()


def test_seasonal_needs_two_years():
    m = fit_demand(seasonal_agg(n=18), "linear", seasonal=True)
    assert m.season is None
    assert any(w.key == "warn_season_short" for w in m.warnings)


def test_bootstrap_range_brackets_the_optimum():
    from optimizer import optimal_price_range

    agg = synthetic_agg(noise=0.05)
    m = fit_demand(agg, "linear")
    p = params(m)
    low, high = optimal_price_range(agg, "linear", p, seed=3)
    assert low < run_scenario(m, p).optimal["price"] < high
    # Less noise, narrower range
    low2, high2 = optimal_price_range(synthetic_agg(noise=0.005), "linear", p, seed=3)
    assert high2 - low2 < (high - low) / 3


def test_bootstrap_matches_full_refit_path():
    """The fast bootstrap must agree with refitting via fit_demand + run_scenario."""
    from optimizer import optimal_price_range

    agg = seasonal_agg(n=30)
    p = params(None, max_price=150)
    rng = np.random.default_rng(7)
    slow = []
    for _ in range(60):
        sample = agg.iloc[rng.integers(0, len(agg), len(agg))]
        try:
            slow.append(run_scenario(fit_demand(sample, "linear", True), p).optimal["price"])
        except ValueError:
            pass
    fast = optimal_price_range(agg, "linear", p, seasonal=True, n=60, seed=7)
    assert fast == pytest.approx(tuple(np.percentile(slow, [5, 95])), rel=1e-6)


# ---------- fees, VAT and extra unit costs ----------

def analytic_optimum(m, cogs, k=1.0):
    """Linear demand with per-unit net price k·P − cogs: P* = (a/(−b) + cogs/k) / 2."""
    a_eff = m.intercept + m.c * 50.0
    return (a_eff / -m.b + cogs / k) / 2


@pytest.mark.parametrize("fees", [dict(commission=0.2), dict(vat=0.2), dict(vat=0.2, commission=0.15, payment_fee=0.02)])
def test_fees_and_vat_match_analytic_optimum(fees):
    m = fit_demand(synthetic_agg(), "linear")
    p = params(m, **fees)
    r = run_scenario(m, p)
    k = 1 / (1 + p.vat) - p.fee_rate
    step = r.curve["price"].iloc[1] - r.curve["price"].iloc[0]
    assert r.optimal["price"] == pytest.approx(analytic_optimum(m, 20.0, k), abs=step)
    assert r.optimal["price"] > run_scenario(m, params(m)).optimal["price"]


def test_vat_and_fees_come_off_profit():
    m = fit_demand(synthetic_agg(), "linear")
    plain = run_scenario(m, params(m)).baseline
    taxed = run_scenario(m, params(m, vat=0.2, commission=0.1)).baseline
    assert taxed["revenue"] == pytest.approx(plain["revenue"] / 1.2)
    assert taxed["fees"] == pytest.approx(0.1 * 45.0 * plain["q_sold"])
    assert taxed["profit"] == pytest.approx(plain["profit"] - taxed["vat"] - taxed["fees"])
    assert taxed["margin_pct"] == pytest.approx((45 / 1.2 - 4.5 - 20) / (45 / 1.2))


def test_extra_unit_cost_inflates_with_local_inflation():
    p = ScenarioParams(base_cogs=10.0, fixed_monthly=0, capacity=1e9, import_share=0.0, inflation=0.1,
                       extra_unit_cost=2.0)
    assert shocked_costs(p)[0] == pytest.approx(10 * 1.1 + 2 * 1.1)
    m = fit_demand(synthetic_agg(), "linear")
    assert run_scenario(m, params(m, extra_unit_cost=5)).optimal["price"] > run_scenario(m, params(m)).optimal["price"]


def test_bootstrap_range_brackets_optimum_with_fees():
    from optimizer import optimal_price_range

    agg = synthetic_agg(noise=0.05)
    m = fit_demand(agg, "linear")
    p = params(m, commission=0.2, vat=0.2)
    low, high = optimal_price_range(agg, "linear", p, seed=3)
    assert low < run_scenario(m, p).optimal["price"] < high


# ---------- guardrails ----------

def guarded(rails, **kw):
    from optimizer import recommend

    m = fit_demand(synthetic_agg(), "linear")
    p = params(m, **kw)
    r = run_scenario(m, p)
    return r, recommend(m, p, r, rails)


def test_guardrails_off_return_the_optimum():
    from optimizer import Guardrails

    r, rec = guarded(Guardrails(max_change=0))
    assert rec.price == r.optimal["price"] and rec.binding == [] and rec.warnings == []


def test_max_change_clamps_the_step():
    from optimizer import Guardrails

    r, rec = guarded(Guardrails(max_change=0.05), current_price=30.0)  # optimum ≈ 42, far above +5%
    step = r.curve["price"].iloc[1] - r.curve["price"].iloc[0]
    assert rec.price == pytest.approx(31.5, abs=step)
    assert rec.price <= 31.5
    assert rec.binding == ["max_change"]
    assert rec.row["profit"] < r.optimal["profit"]


def test_floor_and_ceiling():
    from optimizer import Guardrails

    _, high = guarded(Guardrails(max_change=0, floor=50.0))
    assert high.price == 50.0 and high.binding == ["floor"]  # exactly the floor, not the next grid point
    _, low = guarded(Guardrails(max_change=0, ceiling=35.0))
    assert low.price == 35.0 and low.binding == ["ceiling"]


def test_min_margin_is_respected():
    from optimizer import Guardrails

    r, rec = guarded(Guardrails(max_change=0, min_margin=0.6))
    assert r.optimal["margin_pct"] < 0.6
    assert rec.row["margin_pct"] >= 0.6 - 1e-9
    assert "min_margin" in rec.binding


def test_unreachable_margin_falls_back_to_band_with_warning():
    from optimizer import Guardrails

    _, rec = guarded(Guardrails(max_change=0.05, min_margin=0.9))
    assert 45 * 0.95 - 1e-9 <= rec.price <= 45 * 1.05 + 1e-9
    assert [w.key for w in rec.warnings] == ["warn_guardrail_margin"]
    assert "min_margin" not in rec.binding  # dropped, so it isn't what limits the price


def test_floor_outside_step_band_warns():
    from optimizer import Guardrails

    _, rec = guarded(Guardrails(max_change=0.05, floor=60.0))
    assert rec.price >= 60.0
    assert [w.key for w in rec.warnings] == ["warn_guardrail_conflict"]


@pytest.mark.parametrize("ending,cents", [(".99", 99), (".90", 90), ("whole", 0)])
def test_price_endings(ending, cents):
    from optimizer import Guardrails

    r, rec = guarded(Guardrails(max_change=0, ending=ending))
    assert round(rec.price * 100) % 100 == cents
    assert abs(rec.price - r.optimal["price"]) < 1.0
    assert rec.row["profit"] == pytest.approx(
        run_scenario(fit_demand(synthetic_agg(), "linear"), params(None, current_price=rec.price)).baseline["profit"])


# ---------- stockout / promo flags ----------

def stockout_daily(flag: bool, seed=1):
    """Daily sales over 24 months with true demand Q/day = 120 − 2P. In cheap (busy) months stock runs
    out at 35 units/day, so recorded sales understate demand; with `flag`, those days are marked."""
    from data_ingestion import aggregate

    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
    month_price = {m: rng.uniform(30, 55) for m in dates.to_period("M").unique()}
    price = np.array([month_price[m] for m in dates.to_period("M")])
    demand = 120 - 2 * price + rng.normal(0, 3, len(dates))
    sold = np.minimum(demand, 35)
    df = pd.DataFrame({"Date": dates, "Price_Charged": price, "Quantity_Sold": sold, "Cost_Per_Unit": 20.0,
                       "Flag": np.where(flag & (demand > 35), "stockout", "")})
    return aggregate(df)[0]


def test_stockouts_bias_slope_unless_flagged():
    true_monthly_slope = -2 * 30.4
    unflagged = fit_demand(stockout_daily(flag=False), "linear")
    flagged = fit_demand(stockout_daily(flag=True), "linear")
    assert unflagged.b > true_monthly_slope * 0.6  # biased toward zero: looks price-insensitive
    assert flagged.b == pytest.approx(true_monthly_slope, rel=0.15)


def test_excluded_months_are_skipped_by_fit_and_bootstrap():
    from optimizer import optimal_price_range

    clean = synthetic_agg(noise=0.05)
    dirty = pd.concat([clean, clean.iloc[:4].set_axis(pd.date_range("2027-01-01", periods=4, freq="MS"))
                       .assign(Quantity_Sold=0.0)])
    dirty["Excluded"] = [False] * len(clean) + [True] * 4
    m_clean, m_dirty = fit_demand(clean, "linear"), fit_demand(dirty, "linear")
    assert (m_dirty.b, m_dirty.n) == (pytest.approx(m_clean.b), m_clean.n)
    p = params(m_clean)
    assert optimal_price_range(dirty, "linear", p, seed=1) == optimal_price_range(clean, "linear", p, seed=1)


# ---------- rolling backtest ----------

def test_backtest_on_noiseless_data_is_exact_and_beats_naive():
    from optimizer import backtest

    bt = backtest(synthetic_agg(), "linear")
    assert len(bt.months) == 6 and bt.months[-1] == synthetic_agg().index[-1]
    assert bt.wape == pytest.approx(0, abs=1e-9)
    assert bt.naive_wape > 0.05 and bt.beats_naive
    assert bt.naive.tolist() == synthetic_agg()["Quantity_Sold"].iloc[-7:-1].tolist()


def test_backtest_never_trains_on_the_month_it_forecasts(monkeypatch):
    import optimizer

    seen = []
    real_fit = optimizer.fit_demand
    monkeypatch.setattr(optimizer, "fit_demand", lambda agg, *a, **k: seen.append(agg.index.max()) or real_fit(agg, *a, **k))
    agg = synthetic_agg(noise=0.05)
    bt = optimizer.backtest(agg, "linear")
    assert seen == list(agg.index[-7:-1])  # each fit ends the month before its forecast
    assert bt.wape > 0


def test_backtest_shrinks_horizon_then_gives_up():
    from optimizer import backtest

    # Linear with competitor needs 4 training months: 8 months leave room for 4 forecasts,
    # 6 months for only 2, below the 3-month minimum
    assert len(backtest(synthetic_agg(n=8), "linear").months) == 4
    assert backtest(synthetic_agg(n=6), "linear") is None


def test_backtest_skips_excluded_months():
    from optimizer import backtest

    agg = synthetic_agg(noise=0.05)
    agg["Excluded"] = False
    agg.iloc[-2, agg.columns.get_loc("Excluded")] = True
    bt = backtest(agg, "linear")
    assert agg.index[-2] not in bt.months and len(bt.months) == 6


def test_fit_reports_residual_sd():
    noiseless, noisy = fit_demand(synthetic_agg(), "linear"), fit_demand(synthetic_agg(noise=0.05), "linear")
    assert noiseless.resid_sd == pytest.approx(0, abs=1e-6)
    assert noisy.resid_sd > 10


# ---------- price test plan ----------
# Imported inside each test: pytest would otherwise collect optimizer.test_plan / TestPlan as tests.

def plan_for(rec_price=50.0, noise=60.0, **kw):
    import optimizer

    m = fit_demand(synthetic_agg(), "linear")
    p = params(m, **kw)
    return m, p, optimizer.test_plan(m, p, rec_price, rec_price, noise, optimizer.Guardrails(max_change=0))


def test_plan_weeks_follow_power_formula():
    from optimizer import WEEKS_PER_MONTH, Z90, Z_POWER

    m, p, plan = plan_for(rec_price=50.0, noise=60.0)
    weekly = lambda price: m.predict(price, 50.0) / WEEKS_PER_MONTH
    assert plan.expected_test == pytest.approx(weekly(50.0)) and plan.expected_current == pytest.approx(weekly(45.0))
    sd_week = 60.0 / np.sqrt(WEEKS_PER_MONTH)
    per_arm = np.ceil(2 * (Z90 + Z_POWER) ** 2 * sd_week ** 2 / plan.diff ** 2)
    assert plan.weeks == max(4, 2 * per_arm)
    assert plan.schedule["arm"].tolist()[:3] == ["test", "current", "test"]
    assert plan.schedule["price"].tolist()[:2] == [50.0, 45.0]
    row = plan.schedule.iloc[0]
    assert row["high"] - row["expected"] == pytest.approx(Z90 * sd_week)


def test_plan_clamps_weeks_and_warns_when_underpowered():
    _, _, quiet = plan_for(noise=1.0)
    assert quiet.weeks == 4 and quiet.warnings == []
    _, _, noisy = plan_for(noise=5000.0)
    assert noisy.weeks == 24
    assert [w.key for w in noisy.warnings] == ["warn_test_underpowered"]


def test_small_recommended_move_tests_a_five_percent_step():
    import optimizer

    m = fit_demand(synthetic_agg(), "linear")
    p = params(m)  # current price 45
    up = optimizer.test_plan(m, p, 45.2, 48.0, 60.0, optimizer.Guardrails(max_change=0))
    down = optimizer.test_plan(m, p, 45.0, 40.0, 60.0, optimizer.Guardrails(max_change=0, ending=".99"))
    assert up.test_price == pytest.approx(47.25)
    assert down.test_price == 42.99  # 42.75 rounded to the nearest .99 ending


def test_weekly_expectation_respects_capacity():
    _, _, plan = plan_for(capacity=1000.0)  # monthly capacity → ~230 per week
    assert plan.expected_current == pytest.approx(1000.0 * 12 / 52)


def verdict(plan, test_shift=0.0, both_shift=0.0, weeks=None):
    from optimizer import evaluate_test

    s = plan.schedule.head(weeks) if weeks else plan.schedule
    actual = s["expected"] + both_shift + np.where(s["arm"] == "test", test_shift, 0.0)
    return evaluate_test(plan, list(actual) + [None] * (plan.weeks - len(s)))


def test_evaluate_needs_two_weeks_per_arm():
    _, _, plan = plan_for()
    assert verdict(plan, weeks=3) is None
    assert verdict(plan, weeks=4) is not None


def test_verdict_codes():
    _, _, plan = plan_for(rec_price=50.0, noise=20.0)  # test price above current: fewer units expected
    assert verdict(plan).code == "consistent"
    assert verdict(plan, test_shift=-3 * abs(plan.diff)).code == "more_sensitive"
    assert verdict(plan, test_shift=+abs(plan.diff)).code == "less_sensitive"  # no drop at all
    v = verdict(plan, both_shift=0.3 * plan.expected_current)  # season shift hits both arms
    assert v.code == "consistent" and v.level_ratio > 1.2
    assert verdict(plan).elasticity_observed == pytest.approx(verdict(plan).elasticity_model)
