"""Demand estimation, elasticities and the shock-aware profit optimizer.

Pipeline (Steps refer to the architecture guide):
  1. Monthly aggregation + period multiplier       (data_ingestion.aggregate, PERIOD_MULT)
  2. Demand fit: linear or log-log OLS              (fit_demand)
  3. PED / XED                                      (elasticities)
  4. Competitor price shock                         (run_scenario)
  5. Capacity cap                                   (run_scenario)
  6. FX shock on the imported share of COGS         (shocked_costs)
  7. Inflation on COGS and fixed costs              (shocked_costs)
  8. Profit sweep over a 2,000-point price grid     (run_scenario)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from config import PERIOD_MULT, PRICE_GRID_POINTS
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

    @property
    def has_comp(self) -> bool:
        return self.c is not None

    def predict(self, price, comp_price: float | None = None) -> np.ndarray:
        """Monthly quantity demanded at `price` (scalar or array)."""
        p = np.asarray(price, dtype=float)
        if self.kind == "linear":
            q = self.intercept + self.b * p
            if self.has_comp:
                q = q + self.c * comp_price
            return np.maximum(0.0, q)
        log_q = self.intercept + self.b * np.log(np.maximum(p, 1e-9))
        if self.has_comp:
            log_q = log_q + self.c * np.log(max(comp_price, 1e-9))
        return np.exp(log_q)

    def equation(self, symbol: str = "") -> str:
        comp = self.has_comp
        if self.kind == "linear":
            s = f"Q = {self.intercept:,.2f} {self.b:+,.3f}·P"
            return s + (f" {self.c:+,.3f}·P_comp" if comp else "")
        s = f"ln Q = {self.intercept:,.3f} {self.b:+,.3f}·ln P"
        return s + (f" {self.c:+,.3f}·ln P_comp" if comp else "")


def fit_demand(agg: pd.DataFrame, kind: str = "linear") -> DemandModel:
    """OLS fit of monthly quantity on real price (and real competitor price if present)."""
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

    if len(data) < len(cols) + 2:
        raise ValueError(Msg("err_not_enough_periods", n=len(data), kind=kind))

    reg = LinearRegression().fit(X, y)
    model = DemandModel(
        kind=kind,
        intercept=float(reg.intercept_),
        b=float(reg.coef_[0]),
        c=float(reg.coef_[1]) if comp_col else None,
        r2=0.0,
        n=len(data),
        n_dropped=n_dropped,
        p_min=float(data[price_col].min()),
        p_max=float(data[price_col].max()),
        warnings=warnings,
    )

    q_actual = data["Quantity_Sold"].values
    q_hat = np.array([
        model.predict(p, pc) for p, pc in zip(data[price_col], data[comp_col] if comp_col else [None] * len(data))
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
    """Steps 6-7: FX hits only the imported share of COGS; inflation hits all costs."""
    cogs_fx = p.base_cogs * (1 + p.import_share * p.fx_shift)
    cogs_final = cogs_fx * (1 + p.inflation)
    fixed_final = p.fixed_monthly * (1 + p.inflation) * PERIOD_MULT[p.period]
    return cogs_final, fixed_final


def _economics(model, price, comp_price, cogs, fixed, capacity, mult) -> dict:
    q_demand = model.predict(price, comp_price) * mult
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


def run_scenario(model: DemandModel, p: ScenarioParams) -> ScenarioResult:
    mult = PERIOD_MULT[p.period]
    warnings: list[str] = []

    # Step 4: competitor shock (predict directly with the shifted competitor price)
    comp_price = p.base_comp_price * (1 + p.comp_shift) if model.has_comp else None

    # Steps 6-7
    cogs_final, fixed_final = shocked_costs(p)

    # Step 8: grid scales with price level, so it works for $5 items and ₺50,000 items alike
    low = max(0.01, min(cogs_final, p.current_price) * 0.9)
    high = max(p.max_price, low * 1.5)
    grid = np.linspace(low, high, PRICE_GRID_POINTS)

    curve = pd.DataFrame(_economics(model, grid, comp_price, cogs_final, fixed_final, p.capacity, mult))
    i = int(curve["profit"].idxmax())
    optimal = curve.iloc[i].to_dict()
    baseline = {
        k: float(v)
        for k, v in _economics(
            model, np.array(p.current_price), comp_price, cogs_final, fixed_final, p.capacity, mult
        ).items()
    }

    ped_opt, xed_opt = elasticities(model, optimal["price"], comp_price)
    ped_current, _ = elasticities(model, p.current_price, comp_price)

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
    if not (model.p_min <= optimal["price"] <= model.p_max):
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
