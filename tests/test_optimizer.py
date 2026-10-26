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
