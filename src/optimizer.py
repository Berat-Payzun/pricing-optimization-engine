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
     demand is evaluated at the real price P / (1 + inflation)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from config import BOOTSTRAP_SAMPLES, PERIOD_MULT, PRICE_GRID_POINTS, SEASONAL_MIN_MONTHS
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
    the local share and fixed costs with local inflation."""
    imported = p.import_share * (1 + p.fx_shift) * (1 + p.usd_inflation)
    local = (1 - p.import_share) * (1 + p.inflation)
    cogs_final = p.base_cogs * (imported + local)
    fixed_final = p.fixed_monthly * (1 + p.inflation) * PERIOD_MULT[p.period]
    return cogs_final, fixed_final


def _economics(model, price, comp_price, cogs, fixed, capacity, mult, level=1.0) -> dict:
    """`price` is nominal; demand responds to the real price `price / level`."""
    q_demand = model.predict(price / level, comp_price) * mult
    q_sold = np.minimum(q_demand, capacity)
    revenue = price * q_sold
    var_cost = cogs * q_sold
    total_cost = var_cost + fixed
    return {
        "price": price,
        "q_demand": q_demand,
        "q_sold": q_sold,
        "revenue": revenue,
        "var_cost": var_cost,
        "total_cost": total_cost,
        "profit": revenue - total_cost,
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

    curve = pd.DataFrame(_economics(model, grid, comp_real, cogs_final, fixed_final, p.capacity, mult, level))
    i = int(curve["profit"].idxmax())
    optimal = curve.iloc[i].to_dict()
    # Baseline keeps today's nominal price, which is a real price cut under pass-through
    baseline = {
        k: float(v)
        for k, v in _economics(
            model, np.array(p.current_price), comp_real, cogs_final, fixed_final, p.capacity, mult, level
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
                            s.level)["profit"]
        prices.append(s.grid[int(np.argmax(profit))])
    if len(prices) < n / 2:
        return None
    tail = (1 - coverage) / 2 * 100
    low, high = np.percentile(prices, [tail, 100 - tail])
    return float(low), float(high)
