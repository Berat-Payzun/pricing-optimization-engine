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
