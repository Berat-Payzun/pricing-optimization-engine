import io

import numpy as np
import pandas as pd
import pytest

from data_ingestion import load_csv
from optimizer import Guardrails
from portfolio import COLUMNS, portfolio

SHARED = dict(period="Monthly", import_share=0.0, fee_rate=0.0, vat=0.0, extra_unit_cost=0.0,
              comp_match_cut=0.0, comp_match_rise=0.0)


def multi_product_rows():
    """A and B: 24 months of linear demand (A with competitor prices, B without); C: 2 months only."""
    rng = np.random.default_rng(0)
    lines = ["Date,Product,Price_Charged,Quantity_Sold,Cost_Per_Unit,Competitor_Price"]
    for d in pd.date_range("2024-01-01", periods=24, freq="MS"):
        pa, pb, pc = rng.uniform(30, 60), rng.uniform(15, 30), rng.uniform(40, 55)
        lines.append(f"{d.date()},A,{pa:.2f},{3000 - 60 * pa + 30 * pc:.0f},20,{pc:.2f}")
        lines.append(f"{d.date()},B,{pb:.2f},{1500 - 40 * pb:.0f},8,")
    lines += ["2024-01-01,C,10,100,5,", "2024-02-01,C,11,95,5,"]
    rows, _ = load_csv(io.StringIO("\n".join(lines)), default_cogs=5)
    return rows


def test_every_product_gets_a_row_and_a_failed_one_explains_why():
    pf = portfolio(multi_product_rows(), None, "auto", False, False, SHARED, Guardrails(max_change=0))
    assert list(pf.columns) == COLUMNS and pf["product"].tolist() == ["A", "B", "C"]
    a, b, c = (pf.iloc[i] for i in range(3))
    assert a["status"] == b["status"] == "ok" and c["status"] == "error"
    assert c["error"].key == "err_too_few_months"
    # A's true optimum with no fixed costs: P* = (a + c·Pc)/(−2b) + cogs/2 at the latest competitor price
    assert a["rec_price"] > a["current_price"] * 0.5 and a["uplift"] >= -1e-6 and b["uplift"] >= -1e-6
    assert a["model"] in ("linear", "loglog") and np.isfinite(a["wape"])


def test_guardrails_and_contribution_apply_to_every_product():
    rails = Guardrails(max_change=0.05, ending=".99")
    pf = portfolio(multi_product_rows(), None, "linear", False, False, SHARED, rails).iloc[:2]
    assert (pf["change"].abs() <= 0.05 + 0.02).all()  # within ±5%, plus rounding to .99
    assert all(f"{p:.2f}".endswith(".99") for p in pf["rec_price"])
    assert (pf["model"] == "linear").all()


def test_products_without_sales_or_without_a_profitable_price_say_so():
    lines = ["Date,Product,Price_Charged,Quantity_Sold,Cost_Per_Unit"]
    for i, d in enumerate(pd.date_range("2024-01-01", periods=12, freq="MS")):
        lines.append(f"{d.date()},Dead,{10 + i},0,5")  # never sold
        lines.append(f"{d.date()},Costly,{20 + i},{600 - 20 * (20 + i)},500")  # costs more than anyone pays
    rows, _ = load_csv(io.StringIO("\n".join(lines)), default_cogs=5)
    pf = portfolio(rows, None, "linear", False, False, SHARED, Guardrails()).set_index("product")
    assert pf.loc["Dead", "status"] == "error" and pf.loc["Dead", "error"].key == "err_no_sales"
    assert pf.loc["Costly", "status"] == "no_profit"


def test_unit_cost_is_in_the_same_money_as_the_price_when_last_months_are_excluded():
    from data_ingestion import aggregate, deflate
    from optimizer import fit_demand
    from portfolio import product_inputs

    idx = pd.date_range("2023-01-01", periods=24, freq="MS")
    price = np.random.default_rng(1).uniform(40, 60, 24)
    rows = pd.DataFrame({"Date": idx, "Price_Charged": price, "Quantity_Sold": 3000 - 40 * price,
                         "Cost_Per_Unit": 20.0, "Flag": [""] * 22 + ["promo"] * 2})
    cpi = pd.Series(1.03 ** np.arange(24), index=idx)  # 3% a month
    agg, _ = deflate(aggregate(rows)[0], cpi)
    current, cogs, _ = product_inputs(agg, fit_demand(agg))
    assert current == pytest.approx(price[21] * 1.03 ** 2)
    assert cogs == pytest.approx(20.0 * 1.03 ** 2)  # deflated like the price, not the nominal 20


def test_pricing_step_reuses_the_fits():
    from portfolio import fit_products, price_products

    rows = multi_product_rows()
    fits = fit_products(rows, None, "auto", False, False)
    assert list(fits) == ["A", "B", "C"] and fits["C"].error.key == "err_too_few_months"
    shared = {**SHARED, "fee_rate": 0.1}
    for rails in (Guardrails(max_change=0), Guardrails(max_change=0.05)):
        expected = portfolio(rows, None, "auto", False, False, shared, rails)
        pd.testing.assert_frame_equal(price_products(fits, shared, rails), expected)
