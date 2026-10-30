"""Demand estimation, elasticities and the shock-aware profit optimizer.

Pipeline (Steps refer to the architecture guide):
  1. Monthly aggregation + period multiplier       (data_ingestion.aggregate, PERIOD_MULT)
  2. Demand fit: linear or log-log OLS              (fit_demand)
  3. PED / XED                                      (elasticities)
  4. Competitor price shock                         (run_scenario)
  5. Capacity cap                                   (run_scenario)
  6. FX + USD inflation on the imported COGS share  (shocked_costs)
  7. Local inflation on the rest of COGS and fixed  (shocked_costs)
  8. Profit sweep over a 2,000-point price grid     (run_scenario); with price pass-through,
     demand is evaluated at the real price P / (1 + inflation). VAT inside the price and
     price-based fees (commission, payment) come off each unit's revenue.
  9. Guardrails on the recommendation               (recommend): max step, min margin,
     floor/ceiling and price endings
Model checking: a rolling out-of-sample backtest (backtest) and a price test plan that alternates the
current and a test price week by week (test_plan, evaluate_test).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from config import (BACKTEST_MIN_MONTHS, BACKTEST_MONTHS, BOOTSTRAP_SAMPLES, PERIOD_MULT, PRICE_GRID_POINTS,
                    SEASONAL_MIN_MONTHS, TEST_DEFAULT_STEP, TEST_MAX_WEEKS, TEST_MIN_WEEKS, TEST_STEP_CHOICES)
from translations import Msg


@dataclass
class DemandModel:
    kind: str  # "linear" | "loglog"
    intercept: float
    b: float  # own-price coefficient
    c: float | None  # competitor-price coefficient (None if no competitor data)
    r2: float  # R² on quantity levels, comparable across both model kinds
    n: int
    n_dropped: int  # periods excluded from a log-log fit (zero sales / non-positive prices)
    p_min: float
    p_max: float
    warnings: list[str] = field(default_factory=list)
    # Month-of-year effects (Jan..Dec, mean zero; in log units for log-log) or None. The
    # intercept is for an average month, so the optimizer prices for a typical month.
    season: np.ndarray | None = None
    resid_sd: float = 0.0  # in-sample SD of monthly quantity residuals (degrees-of-freedom adjusted)

    @property
    def has_comp(self) -> bool:
        return self.c is not None

    def predict(self, price, comp_price: float | None = None, month: int | None = None) -> np.ndarray:
        """Monthly quantity demanded at `price` (scalar or array), for an average month
        unless `month` (1-12) is given and the model is seasonal."""
        p = np.asarray(price, dtype=float)
        s = self.season[month - 1] if self.season is not None and month is not None else 0.0
        if self.kind == "linear":
            q = self.intercept + s + self.b * p
            if self.has_comp:
                q = q + self.c * comp_price
            return np.maximum(0.0, q)
        log_q = self.intercept + s + self.b * np.log(np.maximum(p, 1e-9))
        if self.has_comp:
            log_q = log_q + self.c * np.log(max(comp_price, 1e-9))
        return np.exp(log_q)

    def equation(self, symbol: str = "") -> str:
        comp, season = self.has_comp, " + s(month)" if self.season is not None else ""
        if self.kind == "linear":
            s = f"Q = {self.intercept:,.2f} {self.b:+,.3f}·P"
            return s + (f" {self.c:+,.3f}·P_comp" if comp else "") + season
        s = f"ln Q = {self.intercept:,.3f} {self.b:+,.3f}·ln P"
        return s + (f" {self.c:+,.3f}·ln P_comp" if comp else "") + season


def month_dummies(index: pd.DatetimeIndex) -> np.ndarray:
    """One column per month Feb..Dec (January is the base)."""
    return (np.asarray(index.month)[:, None] == np.arange(2, 13)).astype(float)


@dataclass
class _Design:
    """Regression inputs shared by fit_demand and the bootstrap."""
    data: pd.DataFrame
    price_col: str
    comp_col: str | None
    X: np.ndarray
    y: np.ndarray
    n_dropped: int
    use_season: bool
    warnings: list[str]


def _design(agg: pd.DataFrame, kind: str, seasonal: bool) -> _Design:
    if "Excluded" in agg:  # stockout / promo months (data_ingestion.aggregate)
        agg = agg[~agg["Excluded"].astype(bool)]
    price_col = "Real_Price" if "Real_Price" in agg else "Price_Charged"
    comp_col = "Real_Competitor_Price" if "Real_Competitor_Price" in agg else (
        "Competitor_Price" if "Competitor_Price" in agg else None
    )
    cols = [price_col] + ([comp_col] if comp_col else [])
    data = agg[cols + ["Quantity_Sold"]].dropna()
    warnings: list[str] = []

    n_dropped = 0
    if kind == "loglog":
        mask = (data[cols] > 0).all(axis=1) & (data["Quantity_Sold"] > 0)
        n_dropped = int((~mask).sum())
        data = data[mask]
        if n_dropped:
            warnings.append(Msg("warn_loglog_dropped", n_dropped=n_dropped, total=n_dropped + len(data)))
        X, y = np.log(data[cols].values), np.log(data["Quantity_Sold"].values)
    else:
        X, y = data[cols].values, data["Quantity_Sold"].values

    use_season = seasonal and len(data) >= SEASONAL_MIN_MONTHS
    if seasonal and not use_season:
        warnings.append(Msg("warn_season_short", n=len(data), min_n=SEASONAL_MIN_MONTHS))
    if use_season:
        X = np.hstack([X, month_dummies(data.index)])

    if len(data) < X.shape[1] + 2:
        raise ValueError(Msg("err_not_enough_periods", n=len(data), kind=kind))
    return _Design(data, price_col, comp_col, X, y, n_dropped, use_season, warnings)


def _model(d: _Design, kind: str, intercept: float, coef: np.ndarray, warnings: list[str]) -> DemandModel:
    """Build a DemandModel from regression coefficients (price, [competitor], [Feb..Dec])."""
    n_prices = 2 if d.comp_col else 1
    season = None
    if d.use_season:
        effects = np.concatenate([[0.0], coef[n_prices:]])  # January = base month
        intercept += float(effects.mean())
        season = effects - effects.mean()
    return DemandModel(
        kind=kind,
        intercept=float(intercept),
        b=float(coef[0]),
        c=float(coef[1]) if d.comp_col else None,
        r2=0.0,
        n=len(d.data),
        n_dropped=d.n_dropped,
        p_min=float(d.data[d.price_col].min()),
        p_max=float(d.data[d.price_col].max()),
        warnings=warnings,
        season=season,
    )


def fit_demand(agg: pd.DataFrame, kind: str = "linear", seasonal: bool = False) -> DemandModel:
    """OLS fit of monthly quantity on real price (and real competitor price if present),
    optionally with month-of-year effects so seasonal swings aren't read as price effects."""
    d = _design(agg, kind, seasonal)
    reg = LinearRegression().fit(d.X, d.y)
    model = _model(d, kind, reg.intercept_, reg.coef_, d.warnings)
    data, price_col, comp_col = d.data, d.price_col, d.comp_col

    q_actual = data["Quantity_Sold"].values
    comps = data[comp_col] if comp_col else [None] * len(data)
    q_hat = np.array([
        model.predict(p, pc, month) for p, pc, month in zip(data[price_col], comps, data.index.month)
    ])
    ss_res = float(((q_actual - q_hat) ** 2).sum())
    ss_tot = float(((q_actual - q_actual.mean()) ** 2).sum())
    model.r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    model.resid_sd = float(np.sqrt(ss_res / max(len(q_actual) - d.X.shape[1] - 1, 1)))

    if model.b >= 0:
        model.warnings.append(Msg("warn_upward_slope"))
    if kind == "loglog" and -1 < model.b < 0:
        model.warnings.append(Msg("warn_inelastic", b=model.b))
    return model


def elasticities(model: DemandModel, price: float, comp_price: float | None) -> tuple[float, float | None]:
    """Point price elasticity (PED) and cross-price elasticity (XED)."""
    if model.kind == "loglog":
        return model.b, model.c
    q = float(model.predict(price, comp_price))
    if q <= 0:
        return float("nan"), (float("nan") if model.has_comp else None)
    ped = model.b * price / q
    xed = model.c * comp_price / q if model.has_comp else None
    return ped, xed


@dataclass
class ScenarioParams:
    base_cogs: float
    fixed_monthly: float
    capacity: float  # units available per selected period
    period: str = "Monthly"
    import_share: float = 0.0  # fraction of COGS priced in USD (0-1)
    fx_shift: float = 0.0  # fraction, + = local currency weakens
    inflation: float = 0.0  # fraction
    comp_shift: float = 0.0  # fraction
    base_comp_price: float | None = None
    current_price: float = 0.0
    max_price: float = 0.0
    usd_inflation: float = 0.0  # fraction: inflation of the USD-priced inputs
    # True: general inflation also lifts willingness to pay and the competitor's price, so
    # demand is evaluated at real prices (price / (1 + inflation)). False: only costs rise.
    price_passthrough: bool = False
    # Sales channel economics. Fees are charged on the customer-facing (VAT-inclusive) price;
    # vat is the rate contained in the price (0 when prices are net of VAT).
    commission: float = 0.0  # fraction of price, e.g. marketplace commission
    payment_fee: float = 0.0  # fraction of price
    vat: float = 0.0  # fraction
    extra_unit_cost: float = 0.0  # shipping, packaging etc. per unit, sourced locally

    @property
    def fee_rate(self) -> float:
        return self.commission + self.payment_fee


@dataclass
class ScenarioResult:
    curve: pd.DataFrame
    optimal: dict
    baseline: dict
    cogs_final: float
    fixed_final: float
    comp_price: float | None
    ped_opt: float
    xed_opt: float | None
    ped_current: float
    break_evens: list[float]
    warnings: list[str]


def shocked_costs(p: ScenarioParams) -> tuple[float, float]:
    """Steps 6-7: the imported (USD-priced) share of COGS moves with FX and USD inflation,
    the local share, extra unit costs and fixed costs with local inflation."""
    imported = p.import_share * (1 + p.fx_shift) * (1 + p.usd_inflation)
    local = (1 - p.import_share) * (1 + p.inflation)
    cogs_final = p.base_cogs * (imported + local) + p.extra_unit_cost * (1 + p.inflation)
    fixed_final = p.fixed_monthly * (1 + p.inflation) * PERIOD_MULT[p.period]
    return cogs_final, fixed_final


def _economics(model, price, comp_price, cogs, fixed, capacity, mult, level=1.0, vat=0.0, fee_rate=0.0) -> dict:
    """`price` is nominal and customer-facing; demand responds to the real price `price / level`.
    Revenue is net of the VAT contained in the price; fees are a share of the price."""
    price = np.asarray(price, dtype=float)
    q_demand = model.predict(price / level, comp_price) * mult
    q_sold = np.minimum(q_demand, capacity)
    net_price = price / (1 + vat)
    unit_fees = fee_rate * price
    revenue = net_price * q_sold
    var_cost = cogs * q_sold
    fees = unit_fees * q_sold
    total_cost = var_cost + fees + fixed
    return {
        "price": price,
        "q_demand": q_demand,
        "q_sold": q_sold,
        "revenue": revenue,
        "vat": (price - net_price) * q_sold,
        "fees": fees,
        "var_cost": var_cost,
        "total_cost": total_cost,
        "profit": revenue - total_cost,
        # Net operating margin per unit, as a share of the net-of-VAT price
        "margin_pct": (net_price - unit_fees - cogs) / net_price,
        "cap_binding": q_demand > capacity,
    }


@dataclass
class _Setup:
    level: float  # scenario price level relative to today's money (the demand model's units)
    comp_real: float | None
    cogs_final: float
    fixed_final: float
    grid: np.ndarray


def _setup(has_comp: bool, p: ScenarioParams) -> _Setup:
    level = 1 + p.inflation if p.price_passthrough else 1.0
    # Step 4: competitor shock. comp_real stays in today's money; under pass-through the
    # competitor's nominal price rises with the price level too.
    comp_real = p.base_comp_price * (1 + p.comp_shift) if has_comp else None
    # Steps 6-7
    cogs_final, fixed_final = shocked_costs(p)
    # Step 8: grid scales with price level, so it works for $5 items and ₺50,000 items alike
    low = max(0.01, min(cogs_final, p.current_price) * 0.9)
    high = max(p.max_price, low * 1.5)
    return _Setup(level, comp_real, cogs_final, fixed_final, np.linspace(low, high, PRICE_GRID_POINTS))


def run_scenario(model: DemandModel, p: ScenarioParams) -> ScenarioResult:
    mult = PERIOD_MULT[p.period]
    warnings: list[str] = []

    s = _setup(model.has_comp, p)
    level, comp_real, cogs_final, fixed_final, grid = s.level, s.comp_real, s.cogs_final, s.fixed_final, s.grid
    comp_price = comp_real * level if model.has_comp else None

    curve = pd.DataFrame(_economics(model, grid, comp_real, cogs_final, fixed_final, p.capacity, mult, level,
                                    p.vat, p.fee_rate))
    i = int(curve["profit"].idxmax())
    optimal = curve.iloc[i].to_dict()
    # Baseline keeps today's nominal price, which is a real price cut under pass-through
    baseline = {
        k: float(v)
        for k, v in _economics(
            model, np.array(p.current_price), comp_real, cogs_final, fixed_final, p.capacity, mult, level,
            p.vat, p.fee_rate
        ).items()
    }

    ped_opt, xed_opt = elasticities(model, optimal["price"] / level, comp_real)
    ped_current, _ = elasticities(model, p.current_price / level, comp_real)

    profit = curve["profit"].values
    crossings = np.where(np.diff(np.sign(profit)) != 0)[0]
    break_evens = [
        float(np.interp(0, [profit[j], profit[j + 1]], [grid[j], grid[j + 1]]))
        if profit[j] < profit[j + 1]
        else float(np.interp(0, [profit[j + 1], profit[j]], [grid[j + 1], grid[j]]))
        for j in crossings
    ]

    if i == len(grid) - 1:
        warnings.append(Msg("warn_opt_at_top"))
    if not (model.p_min <= optimal["price"] / level <= model.p_max):  # observed range is in real terms
        warnings.append(Msg("warn_extrapolated", p_min=model.p_min, p_max=model.p_max))
    if optimal["profit"] < 0:
        warnings.append(Msg("warn_loss_only"))
    if bool(optimal["cap_binding"]):
        warnings.append(Msg("warn_cap_binding"))

    return ScenarioResult(
        curve=curve,
        optimal=optimal,
        baseline=baseline,
        cogs_final=cogs_final,
        fixed_final=fixed_final,
        comp_price=comp_price,
        ped_opt=ped_opt,
        xed_opt=xed_opt,
        ped_current=ped_current,
        break_evens=break_evens,
        warnings=warnings,
    )


ENDINGS = ("none", ".99", ".90", "whole")


@dataclass
class Guardrails:
    """Business rules on the recommended price. 0 switches a rule off."""
    max_change: float = 0.15  # max step from the current price, as a fraction
    min_margin: float = 0.0  # min net operating margin per unit (share of the net-of-VAT price)
    floor: float = 0.0
    ceiling: float = 0.0
    ending: str = "none"  # one of ENDINGS


@dataclass
class Recommendation:
    price: float
    row: dict  # economics at `price`, same keys as the curve
    binding: list[str]  # rules the unconstrained optimum broke: "max_change", "min_margin", "floor", "ceiling"
    warnings: list[str]


def _bounds(rails: Guardrails, current_price: float) -> tuple[float, float]:
    """Hard price band from max step, floor and ceiling."""
    low, high = 0.0, np.inf
    if rails.max_change > 0:
        low, high = current_price * (1 - rails.max_change), current_price * (1 + rails.max_change)
    if rails.floor > 0:
        low = max(low, rails.floor)
    if rails.ceiling > 0:
        high = min(high, rails.ceiling)
    return low, high


def _with_ending(price: float, ending: str) -> list[float]:
    """The nearest price points below and above `price` with the given ending."""
    if ending == "whole":
        return [float(np.floor(price)), float(np.ceil(price))]
    cents = {".99": 0.99, ".90": 0.90}[ending]
    base = np.floor(price)
    return [float(base - 1 + cents), float(base + cents)]


def recommend(model: DemandModel, p: ScenarioParams, result: ScenarioResult, rails: Guardrails) -> Recommendation:
    """Step 9: the most profitable price on the scenario's curve that satisfies the guardrails,
    rounded to the chosen price ending."""
    curve, warnings = result.curve, []
    low, high = _bounds(rails, p.current_price)
    if low > high:  # floor above ceiling, or outside the max-step band
        warnings.append(Msg("warn_guardrail_conflict"))
        low, high = _bounds(Guardrails(max_change=0.0, floor=rails.floor, ceiling=rails.ceiling), p.current_price)
        if low > high:
            low, high = 0.0, np.inf

    min_margin = rails.min_margin

    def margin_ok(m):
        return np.asarray(m) >= min_margin - 1e-12 if min_margin > 0 else np.ones_like(m, dtype=bool)

    opt = result.optimal
    binding = [name for name, broken in (
        ("max_change", rails.max_change > 0 and abs(opt["price"] / p.current_price - 1) > rails.max_change + 1e-9),
        ("min_margin", not margin_ok(opt["margin_pct"])),
        ("floor", rails.floor > 0 and opt["price"] < rails.floor),
        ("ceiling", rails.ceiling > 0 and opt["price"] > rails.ceiling),
    ) if broken]

    s = _setup(model.has_comp, p)
    mult = PERIOD_MULT[p.period]

    def evaluate(prices):
        econ = _economics(model, np.asarray(prices, dtype=float), s.comp_real, s.cogs_final, s.fixed_final,
                          p.capacity, mult, s.level, p.vat, p.fee_rate)
        return [{k: (v[i].item() if isinstance(v, np.ndarray) else v) for k, v in econ.items()}
                for i in range(len(prices))]

    def best_in_band() -> dict | None:
        """Best grid point inside the band, or an exact band edge (the grid rarely hits a floor exactly)."""
        feasible = (curve["price"] >= low) & (curve["price"] <= high) & margin_ok(curve["margin_pct"])
        rows = [curve[feasible].loc[curve.loc[feasible, "profit"].idxmax()].to_dict()] if feasible.any() else []
        edges = [e for e in (low, high) if 0 < e < np.inf]
        rows += [r for r in evaluate(edges) if margin_ok(r["margin_pct"])]
        return max(rows, key=lambda r: r["profit"]) if rows else None

    row = best_in_band()
    if row is None and min_margin > 0:
        warnings.append(Msg("warn_guardrail_margin", margin=min_margin * 100))
        min_margin = 0.0  # unreachable inside the price band: keep the band, drop the margin rule
        binding = [b for b in binding if b != "min_margin"]
        row = best_in_band()
    if row is None:  # defensive: the band always has a grid point or a finite edge
        row = evaluate([opt["price"]])[0]
    if rails.ending != "none":
        candidates = [c for c in evaluate([c for c in _with_ending(row["price"], rails.ending) if c > 0])
                      if low - 1e-9 <= c["price"] <= high + 1e-9 and margin_ok(c["margin_pct"])]
        if candidates:
            row = max(candidates, key=lambda c: c["profit"])
        else:
            warnings.append(Msg("warn_guardrail_ending"))
    row = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in row.items()}
    return Recommendation(price=float(row["price"]), row=row, binding=binding, warnings=warnings)


@dataclass
class Backtest:
    months: pd.DatetimeIndex
    actual: np.ndarray
    forecast: np.ndarray
    naive: np.ndarray  # last month's sales carried forward

    @staticmethod
    def _wape(actual, forecast) -> float:
        total = float(np.abs(actual).sum())
        return float(np.abs(actual - forecast).sum()) / total if total > 0 else float("nan")

    @property
    def wape(self) -> float:
        """Weighted absolute % error: Σ|actual − forecast| / Σ actual."""
        return self._wape(self.actual, self.forecast)

    @property
    def naive_wape(self) -> float:
        return self._wape(self.actual, self.naive)

    @property
    def rmse(self) -> float:
        return float(np.sqrt(np.mean((self.actual - self.forecast) ** 2)))

    @property
    def beats_naive(self) -> bool:
        return self.wape < self.naive_wape


def backtest(agg: pd.DataFrame, kind: str, seasonal: bool = False, horizon: int = BACKTEST_MONTHS) -> Backtest | None:
    """Rolling one-month-ahead backtest: each of the last `horizon` months is forecast by a model
    fitted only on the months before it, at the price actually charged. The horizon shrinks to
    BACKTEST_MIN_MONTHS when the earliest training windows are too short to fit; None if even that fails.
    Short windows fall back to a non-seasonal fit, as fit_demand would have done at the time."""
    data = agg[~agg["Excluded"].astype(bool)] if "Excluded" in agg else agg
    price_col = "Real_Price" if "Real_Price" in data else "Price_Charged"
    comp_col = "Real_Competitor_Price" if "Real_Competitor_Price" in data else (
        "Competitor_Price" if "Competitor_Price" in data else None
    )
    for h in range(min(horizon, len(data) - 1), BACKTEST_MIN_MONTHS - 1, -1):
        try:
            forecast = []
            for i in range(len(data) - h, len(data)):
                model = fit_demand(data.iloc[:i], kind, seasonal)
                row = data.iloc[i]
                comp = float(row[comp_col]) if comp_col and model.has_comp else None
                forecast.append(float(model.predict(float(row[price_col]), comp, data.index[i].month)))
        except ValueError:
            continue
        q = data["Quantity_Sold"].to_numpy(dtype=float)
        return Backtest(months=data.index[-h:], actual=q[-h:], forecast=np.array(forecast), naive=q[-h - 1:-1])
    return None


WEEKS_PER_MONTH = 52 / 12
Z90 = 1.645  # two-sided 90% confidence
Z_POWER = 0.8416  # 80% power


@dataclass
class TestPlan:
    current_price: float
    test_price: float
    step: float  # signed fraction requested: + tests a higher price, − a lower one
    weeks: int  # total, half at each price, clamped to TEST_MIN_WEEKS..TEST_MAX_WEEKS
    weeks_needed: float  # unclamped total for 80% power (inf when no difference is expected)
    clipped: bool  # the guardrails held the test price closer to the current price than `step`
    expected_current: float  # weekly units
    expected_test: float
    sd_week: float
    schedule: pd.DataFrame  # week, arm ("test" | "current"), price, expected, low, high
    warnings: list[str]

    @property
    def diff(self) -> float:
        """Expected weekly units at the test price minus at the current price."""
        return self.expected_test - self.expected_current


def _test_price(p: ScenarioParams, step: float, rails: Guardrails) -> tuple[float, bool]:
    """current × (1 + step), kept inside the guardrail band and rounded to the price ending."""
    current = p.current_price
    low, high = _bounds(rails, current)
    wanted = current * (1 + step)
    target = float(np.clip(wanted, low, high))
    clipped = abs(target - wanted) > 1e-9
    if rails.ending != "none":
        candidates = [c for c in _with_ending(target, rails.ending) if low <= c <= high and c > 0]
        if candidates:
            return min(candidates, key=lambda c: abs(c - target)), clipped
    return round(target, 2), clipped


def weeks_needed(diff: float, sd_week: float) -> float:
    """Total weeks (both prices) for 80% power to detect a weekly difference `diff` at 90% confidence."""
    if diff == 0:
        return float("inf")
    return 2 * float(np.ceil(2 * (Z90 + Z_POWER) ** 2 * sd_week ** 2 / diff ** 2))


def test_plan(model: DemandModel, p: ScenarioParams, unconstrained: float, noise_sd_month: float,
              rails: Guardrails, step: float = TEST_DEFAULT_STEP) -> TestPlan:
    """Alternating-weeks price test: the test price (a `step` away from the current price, towards
    the unconstrained optimum) in odd weeks, the current price in even weeks, so season and trend hit
    both alike. The length gives 80% power to detect the predicted difference at 90% confidence,
    from the model's monthly noise. A bigger step means a bigger difference and a shorter test."""
    s = _setup(model.has_comp, p)
    signed = step if unconstrained >= p.current_price else -step
    test_price, clipped = _test_price(p, signed, rails)
    weekly_cap = p.capacity / PERIOD_MULT[p.period] / WEEKS_PER_MONTH

    def weekly(price: float) -> float:  # average month, today's money
        return float(min(model.predict(price / s.level, s.comp_real) / WEEKS_PER_MONTH, weekly_cap))

    exp_cur, exp_test = weekly(p.current_price), weekly(test_price)
    sd_week = noise_sd_month / np.sqrt(WEEKS_PER_MONTH)
    needed = weeks_needed(exp_test - exp_cur, sd_week)
    weeks = int(np.clip(needed, TEST_MIN_WEEKS, TEST_MAX_WEEKS))
    warnings = []
    if clipped:
        warnings.append(Msg("warn_test_step_clipped", step=step * 100, price=test_price))
    if needed > TEST_MAX_WEEKS:
        warnings.append(Msg("warn_test_underpowered", weeks=TEST_MAX_WEEKS))

    arms = np.where(np.arange(weeks) % 2 == 0, "test", "current")
    expected = np.where(arms == "test", exp_test, exp_cur)
    schedule = pd.DataFrame({
        "week": np.arange(1, weeks + 1),
        "arm": arms,
        "price": np.where(arms == "test", test_price, p.current_price),
        "expected": expected,
        "low": np.maximum(expected - Z90 * sd_week, 0.0),
        "high": expected + Z90 * sd_week,
    })
    return TestPlan(p.current_price, test_price, signed, weeks, needed, clipped, exp_cur, exp_test, float(sd_week),
                    schedule, warnings)


def step_tradeoff(model: DemandModel, p: ScenarioParams, unconstrained: float, noise_sd_month: float,
                  rails: Guardrails, steps=TEST_STEP_CHOICES) -> pd.DataFrame:
    """Required test length for a range of step sizes: weeks fall roughly with the square of the step."""
    rows = []
    for step in sorted(set(steps)):
        plan = test_plan(model, p, unconstrained, noise_sd_month, rails, step)
        rows.append({"step": step, "test_price": plan.test_price, "diff": plan.diff,
                     "weeks_needed": plan.weeks_needed, "clipped": plan.clipped})
    return pd.DataFrame(rows)


@dataclass
class TestVerdict:
    code: str  # "consistent" | "more_sensitive" | "less_sensitive"
    observed_diff: float  # mean weekly units, test arm minus current arm
    ci: tuple[float, float]  # 90% interval of observed_diff
    elasticity_observed: float  # arc elasticity between the two prices
    elasticity_model: float
    level_ratio: float  # all observed weeks vs all expected: far from 1 means a season/trend shift


def _arc_elasticity(q_test, q_cur, p_test, p_cur) -> float:
    dq, dp = (q_test - q_cur) / ((q_test + q_cur) / 2), (p_test - p_cur) / ((p_test + p_cur) / 2)
    return dq / dp if dp and (q_test + q_cur) else float("nan")


def evaluate_test(plan: TestPlan, actual) -> TestVerdict | None:
    """Compare entered weekly units with the plan. Needs at least two weeks at each price.
    The price response is judged on the difference between arms, which a common season or
    trend shift cancels out of."""
    a = pd.to_numeric(pd.Series(list(actual), dtype=object), errors="coerce").to_numpy(dtype=float)
    arms = plan.schedule["arm"].to_numpy()
    test, cur = a[(arms == "test") & ~np.isnan(a)], a[(arms == "current") & ~np.isnan(a)]
    if len(test) < 2 or len(cur) < 2:
        return None
    observed = float(test.mean() - cur.mean())
    # Noise from the entered weeks, but never below what the model expects
    sd_t, sd_c = max(test.std(ddof=1), plan.sd_week), max(cur.std(ddof=1), plan.sd_week)
    se = float(np.sqrt(sd_t ** 2 / len(test) + sd_c ** 2 / len(cur)))
    ci = (observed - Z90 * se, observed + Z90 * se)
    if ci[0] <= plan.diff <= ci[1]:
        code = "consistent"
    else:
        # Units lost per unit of price increase: steeper than predicted = more price-sensitive
        slope_obs = observed / (plan.test_price - plan.current_price)
        slope_model = plan.diff / (plan.test_price - plan.current_price)
        code = "more_sensitive" if slope_obs < slope_model else "less_sensitive"
    expected = plan.schedule["expected"].to_numpy()[~np.isnan(a)]
    return TestVerdict(
        code=code,
        observed_diff=observed,
        ci=ci,
        elasticity_observed=_arc_elasticity(test.mean(), cur.mean(), plan.test_price, plan.current_price),
        elasticity_model=_arc_elasticity(plan.expected_test, plan.expected_current, plan.test_price, plan.current_price),
        level_ratio=float(a[~np.isnan(a)].sum() / expected.sum()) if expected.sum() > 0 else float("nan"),
    )


def optimal_price_range(agg: pd.DataFrame, kind: str, params: ScenarioParams, seasonal: bool = False,
                        n: int = BOOTSTRAP_SAMPLES, coverage: float = 0.9, seed: int = 0) -> tuple[float, float] | None:
    """Bootstrap range of P*: refit demand on months resampled with replacement and re-run
    the scenario each time. Returns the central `coverage` interval, or None if fewer than
    half of the resamples could be fitted (e.g. too little price variation)."""
    d = _design(agg, kind, seasonal)  # raises like fit_demand if the data can't be fitted
    s = _setup(d.comp_col is not None, params)
    mult = PERIOD_MULT[params.period]
    rng = np.random.default_rng(seed)
    prices = []
    for _ in range(n):
        idx = rng.integers(0, len(d.y), len(d.y))
        X, y = d.X[idx], d.y[idx]
        if np.ptp(X[:, 0]) < 1e-12:  # no price variation in this resample
            continue
        # Centred least squares, as LinearRegression does: when a resample misses some months
        # the dummies and intercept are collinear, and this picks the same solution sklearn would.
        x_mean, y_mean = X.mean(axis=0), y.mean()
        coef = np.linalg.lstsq(X - x_mean, y - y_mean, rcond=None)[0]
        model = _model(d, kind, y_mean - x_mean @ coef, coef, [])
        profit = _economics(model, s.grid, s.comp_real, s.cogs_final, s.fixed_final, params.capacity, mult,
                            s.level, params.vat, params.fee_rate)["profit"]
        prices.append(s.grid[int(np.argmax(profit))])
    if len(prices) < n / 2:
        return None
    tail = (1 - coverage) / 2 * 100
    low, high = np.percentile(prices, [tail, 100 - tail])
    return float(low), float(high)
