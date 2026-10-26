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


def test_deflate_warns_when_cpi_ends_long_before_sales():
    idx = pd.date_range("2024-01-01", periods=12, freq="MS")
    agg = pd.DataFrame({"Price_Charged": 100.0, "Quantity_Sold": 1}, index=idx)
    cpi = pd.Series([100.0, 101.0, 102.0], index=idx[:3])  # ends 2024-03, sales run to 2024-12
    out, warnings = deflate(agg, cpi)
    assert len(warnings) == 1 and warnings[0].key == "warn_cpi_stale"
    assert "2024-03" in warnings[0]
    assert out["Real_Price"].iloc[-1] == pytest.approx(100.0)


def test_turkish_excel_csv_semicolon_decimal_comma_cp1254():
    text = ("Date;Price_Charged;Quantity_Sold;Cost_Per_Unit\n"
            "01.10.2024;10,50;5;4,25\n"
            "15.10.2024;1.234,56;4;3,9\n"
            "02.11.2024;11;3;Şubat\n")
    df, warnings = load_csv(io.BytesIO(text.encode("cp1254")), default_cogs=7)
    assert df["Date"].tolist() == list(pd.to_datetime(["2024-10-01", "2024-10-15", "2024-11-02"]))  # day first
    assert df["Price_Charged"].tolist() == pytest.approx([10.5, 1234.56, 11.0])
    assert df["Cost_Per_Unit"].tolist() == pytest.approx([4.25, 3.9, 7.0])  # unparseable -> default
    assert any("default COGS" in w for w in warnings)


def test_semicolon_csv_with_dot_decimals_is_not_corrupted():
    df, _ = load_csv(io.BytesIO(b"Date;Price_Charged;Quantity_Sold\n2024-01-01;10.5;5\n"), default_cogs=1)
    assert df["Price_Charged"].iloc[0] == pytest.approx(10.5)


def test_comma_csv_keeps_iso_dates_and_utf8_bom():
    raw = "﻿Date,Price_Charged,Quantity_Sold\n2024-03-04,10.5,5\n".encode("utf-8")
    df, _ = load_csv(io.BytesIO(raw), default_cogs=1)
    assert df["Date"].iloc[0] == pd.Timestamp("2024-03-04")
    assert df["Price_Charged"].iloc[0] == pytest.approx(10.5)


@pytest.mark.parametrize("header, target", [
    ("Tarih", "Date"), ("Satış Fiyatı", "Price_Charged"), ("ADET", "Quantity_Sold"), ("Birim Maliyet", "Cost_Per_Unit"),
    ("Rakip Fiyatı", "Competitor_Price"), ("Ürün", "Product"), ("Datum", "Date"), ("Preis", "Price_Charged"),
    ("Menge", "Quantity_Sold"), ("Stückkosten", "Cost_Per_Unit"), ("Konkurrenzpreis", "Competitor_Price"),
    ("Produkt", "Product"), ("SKU", "Product"), ("Price-Charged", "Price_Charged"),
])
def test_turkish_german_and_english_headers(header, target):
    from data_ingestion import ALIAS_LOOKUP, fold_header

    assert ALIAS_LOOKUP[fold_header(header)] == target


def test_first_matching_header_wins():
    df, _ = load_csv(csv("Date,Price,Price_Charged,Quantity\n2024-01-01,10,99,5"), default_cogs=1)
    assert df["Price_Charged"].iloc[0] == 10


def test_excel_upload_with_turkish_headers_and_products():
    data = pd.DataFrame({
        "Tarih": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01"]),
        "Ürün": ["Kahve", "Çay", "Kahve", None],
        "Fiyat": [10.5, 20.0, 11.0, 21.0],
        "Adet": [5, 3, 4, 2],
        "Rakip Fiyatı": [None, 19.0, 10.0, None],
    })
    buf = io.BytesIO()
    data.to_excel(buf, index=False)
    df, _ = load_csv(io.BytesIO(buf.getvalue()), default_cogs=2)
    assert set(df.columns) >= {"Date", "Product", "Price_Charged", "Quantity_Sold", "Competitor_Price"}
    assert sorted(df["Product"].unique()) == ["Kahve", "Çay", "—"]  # missing product gets a placeholder
    kahve = df[df["Product"] == "Kahve"]
    assert kahve["Price_Charged"].tolist() == pytest.approx([10.5, 11.0])
    # Competitor gaps are filled within the product, not from another product
    assert kahve["Competitor_Price"].tolist() == pytest.approx([10.0, 10.0])
    assert df.loc[df["Product"] == "Çay", "Competitor_Price"].tolist() == pytest.approx([19.0])
