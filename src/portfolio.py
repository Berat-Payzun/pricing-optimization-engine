"""Portfolio view: today's recommended price for every product in a file.

Each product goes through the same pipeline as the single-product view (aggregate → deflate →
fit → scenario → guardrails), with the settings that make sense across products. Fixed costs
are a business-wide figure with no per-product split, so the table compares contribution
(profit before fixed costs), and price floor/ceiling are left out because they are set for
one product.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from data_ingestion import PRODUCT, DataValidationError, aggregate, deflate
from optimizer import (
    DemandModel,
    Guardrails,
    ScenarioParams,
    backtest,
    best_model,
    competitor_price_at,
    elasticities,
    fit_demand,
    recommend,
    run_scenario,
)

COLUMNS = ["product", "months", "model", "current_price", "rec_price", "change", "ped", "contribution_current",
           "contribution_rec", "uplift", "wape", "status", "error"]


def product_inputs(agg: pd.DataFrame, model: DemandModel) -> tuple[float, float, float | None]:
    """Current price, unit cost and competitor price from the latest month in the fit, in the
    model's money (months mostly flagged as stockout/promo never set the current price). The
    cost is deflated like the price, so both are in the same money when the last months are excluded."""
    excluded = agg["Excluded"].astype(bool) if "Excluded" in agg else pd.Series(False, index=agg.index)
    latest = agg[~excluded].iloc[-1]
    factor = float(latest["CPI_Factor"]) if "CPI_Factor" in latest else 1.0
    comp = float(latest["Real_Competitor_Price"]) if model.has_comp else None
    return float(latest["Real_Price"]), float(latest["Cost_Per_Unit"]) * factor, comp


@dataclass
class ProductFit:
    """One product's demand fit: everything in the portfolio row that doesn't depend on fees,
    VAT or guardrails. `error` (a translatable Msg) is set instead when it couldn't be fitted."""
    agg: pd.DataFrame | None = None
    kind: str | None = None
    model: DemandModel | None = None
    wape: float = float("nan")
    error: str | None = None


def fit_products(rows: pd.DataFrame, cpi: pd.Series | None, model_choice: str, seasonal: bool,
                 trend: bool) -> dict[str, ProductFit]:
    """Aggregate, deflate, fit and backtest every product (the slow part of the portfolio).
    `model_choice` is "auto", "linear" or "loglog"."""
    fits = {}
    for product in sorted(rows[PRODUCT].unique()):
        try:
            agg, _ = aggregate(rows[rows[PRODUCT] == product].drop(columns=PRODUCT))
            agg, _ = deflate(agg, cpi)
            models: dict = {}
            for kind in ("linear", "loglog"):
                try:
                    models[kind] = fit_demand(agg, kind, seasonal, trend)
                except ValueError as e:
                    models[kind] = e
            backtests = {k: backtest(agg, k, seasonal, trend=trend) if isinstance(m, DemandModel) else None
                         for k, m in models.items()}
            kind = best_model(models, backtests) if model_choice == "auto" else model_choice
            model = models.get(kind)
            if not isinstance(model, DemandModel):
                raise model if isinstance(model, Exception) else ValueError(str(product))
            bt = backtests[kind]
            fits[product] = ProductFit(agg, kind, model, bt.wape if bt is not None else float("nan"))
        except (DataValidationError, ValueError) as e:
            fits[product] = ProductFit(error=e.args[0] if e.args else str(e))
    return fits


def price_products(fits: dict[str, ProductFit], shared: dict, rails: Guardrails) -> pd.DataFrame:
    """One row per product (see COLUMNS) from fit_products' fits. `shared` holds the ScenarioParams
    fields that apply to every product (period, fees, VAT, import share, extra unit cost,
    competitor reaction). A product that can't be priced gets status "error" and the reason in `error`."""
    out = []
    for product, fit in fits.items():
        row = {"product": product}
        try:
            if fit.error is not None:
                raise ValueError(fit.error)
            agg, kind, model = fit.agg, fit.kind, fit.model
            current, cogs, comp = product_inputs(agg, model)
            p = ScenarioParams(base_cogs=cogs, fixed_monthly=0.0, capacity=np.inf, current_price=current,
                               base_comp_price=comp, max_price=2 * model.p_max, **shared)
            result = run_scenario(model, p)
            rec = recommend(model, p, result, rails)
            row.update(
                months=len(agg), model=kind, current_price=current, rec_price=rec.price,
                change=rec.price / current - 1,
                ped=elasticities(model, rec.price, competitor_price_at(model, p, rec.price))[0],
                contribution_current=result.baseline["profit"], contribution_rec=rec.row["profit"],
                uplift=rec.row["profit"] - result.baseline["profit"],
                wape=fit.wape,
                status="no_profit" if not result.viable else "ok" if result.interior else "no_optimum",
            )
        except (DataValidationError, ValueError) as e:
            row.update(status="error", error=e.args[0] if e.args else str(e))
        out.append(row)
    df = pd.DataFrame(out, columns=COLUMNS)
    # Object column: pandas' string dtype would turn the Msg errors into plain (untranslatable) str
    df["error"] = pd.Series([r.get("error") for r in out], index=df.index, dtype=object)
    return df


def portfolio(rows: pd.DataFrame, cpi: pd.Series | None, model_choice: str, seasonal: bool, trend: bool,
              shared: dict, rails: Guardrails) -> pd.DataFrame:
    """One row per product (see COLUMNS): fit_products, then price_products. The app caches the
    first step on its own, so changing fees or guardrails doesn't refit every product."""
    return price_products(fit_products(rows, cpi, model_choice, seasonal, trend), shared, rails)
