import io

import numpy as np
import pandas as pd
import pytest

from data_ingestion import DataValidationError, aggregate, deflate, load_csv


def csv(text: str) -> io.StringIO:
    return io.StringIO(text.strip())


def test_missing_required_column_raises():
    with pytest.raises(DataValidationError, match="Quantity_Sold"):
        load_csv(csv("Date,Price_Charged\n2024-01-01,10"), default_cogs=5)


def test_column_aliases_and_cost_fallback():
    df, warnings = load_csv(csv("date,Price,qty\n2024-01-01,10,5\n2024-01-02,11,4"), default_cogs=6)
    assert list(df.columns[:3]) == ["Date", "Price_Charged", "Quantity_Sold"]
    assert (df["Cost_Per_Unit"] == 6).all()
    assert any("default COGS" in w for w in warnings)


def test_bad_rows_dropped_and_missing_cost_filled():
    data = """
Date,Price_Charged,Quantity_Sold,Cost_Per_Unit,Competitor_Price
2024-01-01,10,5,4,12
not-a-date,10,5,4,12
2024-01-03,-1,5,4,12
2024-01-04,10,-3,4,
2024-01-05,10,5,,
"""
    df, warnings = load_csv(csv(data), default_cogs=7)
    assert len(df) == 2
    assert df["Cost_Per_Unit"].tolist() == [4, 7]
    assert df["Competitor_Price"].tolist() == [12, 12]  # forward-filled
    assert any("3 of 5 rows dropped" in w for w in warnings)


def daily_frame(months=6, price_by_month=None):
    dates = pd.date_range("2024-01-01", periods=months * 30, freq="D")
    m = dates.month - 1
    prices = np.array(price_by_month or [10 + i for i in range(months)])[m % months]
    return pd.DataFrame({
        "Date": dates,
        "Price_Charged": prices.astype(float),
        "Quantity_Sold": np.full(len(dates), 10),
        "Cost_Per_Unit": 5.0,
    })


def test_aggregate_monthly_weighted_price():
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-01", "2024-01-15", "2024-02-01", "2024-03-01"]),
        "Price_Charged": [10.0, 20.0, 12.0, 14.0],
        "Quantity_Sold": [3, 1, 5, 5],
        "Cost_Per_Unit": [4.0, 6.0, 5.0, 5.0],
    })
    agg, _ = aggregate(df)
    assert len(agg) == 3
    assert agg["Quantity_Sold"].iloc[0] == 4
    assert agg["Price_Charged"].iloc[0] == pytest.approx((10 * 3 + 20 * 1) / 4)
    assert agg["Cost_Per_Unit"].iloc[0] == pytest.approx(5.0)


def test_aggregate_rejects_too_few_periods_and_constant_price():
    with pytest.raises(DataValidationError, match="month"):
        aggregate(daily_frame(months=2))
    with pytest.raises(DataValidationError, match="never varies"):
        aggregate(daily_frame(months=4, price_by_month=[10, 10, 10, 10]))


def test_deflate_rebases_to_latest_month():
    agg = pd.DataFrame(
        {"Price_Charged": [100.0, 100.0, 100.0], "Quantity_Sold": [1, 1, 1]},
        index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
    )
    # CPI ends in February: March reuses February's value (publication lag)
    cpi = pd.Series([100.0, 110.0], index=pd.to_datetime(["2024-01-01", "2024-02-01"]))
    out, warnings = deflate(agg, cpi)
    assert not warnings
    assert out["Real_Price"].tolist() == pytest.approx([110.0, 100.0, 100.0])


def test_deflate_without_cpi_warns():
    agg = pd.DataFrame({"Price_Charged": [1.0], "Quantity_Sold": [1]}, index=pd.to_datetime(["2024-01-01"]))
    out, warnings = deflate(agg, None)
    assert out["Real_Price"].iloc[0] == 1.0
    assert warnings
