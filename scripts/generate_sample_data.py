"""Generate sample_data.csv: daily sales of four products, each with a known demand curve.

The products show off different parts of the app:

- **Classic Mug** (24 months): linear demand with a competitor,
  Q/day = 120 - 2.0*P + 1.0*P_comp + noise, with weekend promos (Flag=promo).
  Its rows are the same as the old single-product sample.
- **Travel Mug** (24 months): constant elasticity -1.8 (log-log), demand growing ~2% a month,
  no competitor prices. "Auto" picks log-log; the growth trend option matters here.
- **Gift Set** (36 months): linear demand with a competitor and a strong Nov/Dec peak,
  Q/day = 60 - 0.8*P + 0.4*P_comp, times the seasonal factor. Has a few stockout days (Flag=stockout).
  The longer history lets the backtest use the month-of-year effects too (they need 24 months).
- **New Tumbler** (2 months): just launched, too few months to price. The "All products"
  table shows the reason instead of a price.

Prices are set once a month, so the monthly aggregates span a wide enough price range to
identify each curve.

Usage:  python scripts/generate_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

START, END = "2024-10-01", "2026-09-30"
SEED = 42

# Classic Mug
TRUE_A, TRUE_B, TRUE_C = 120.0, -2.0, 1.0
# Travel Mug: Q/day = TRAVEL_SCALE * P^TRAVEL_ELASTICITY * (1 + TRAVEL_GROWTH)^month
TRAVEL_ELASTICITY, TRAVEL_SCALE, TRAVEL_GROWTH = -1.8, 40.0 * 30.0 ** 1.8, 0.02
# Gift Set
GIFT_A, GIFT_B, GIFT_C = 60.0, -0.8, 0.4
GIFT_SEASON = {11: 1.3, 12: 1.8, 1: 0.8, 2: 0.85}  # other months 1.0

COLUMNS = ["Date", "Product", "Price_Charged", "Quantity_Sold", "Cost_Per_Unit", "Competitor_Price", "Flag"]


def _days(start=START, end=END):
    dates = pd.date_range(start, end, freq="D")
    return dates, dates.to_period("M")


def _monthly(rng, months, lo, hi):
    """One value per month (a price set at the start of the month), repeated for each day."""
    unique = months.unique()
    per_month = dict(zip(unique, rng.uniform(lo, hi, len(unique)).round(2)))
    return np.array([per_month[m] for m in months])


def _cost(rng, n, base, drift):
    """Unit cost drifting up by `drift` (fraction) over the period, with a little noise."""
    return (base * (1 + drift * np.arange(n) / n) + rng.normal(0, 0.2, n)).round(2)


def classic_mug(seed=SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates, months = _days()
    unique_months = months.unique()

    month_price = dict(zip(unique_months, rng.uniform(38, 62, len(unique_months)).round(2)))
    month_comp = dict(zip(unique_months, rng.uniform(44, 58, len(unique_months)).round(2)))

    price = np.array([month_price[m] for m in months])
    promo = (dates.day_of_week >= 5) & (rng.random(len(dates)) < 0.15)
    price = np.where(promo, (price * 0.9).round(2), price)
    comp = np.array([month_comp[m] for m in months]) + rng.normal(0, 0.5, len(dates)).round(2)

    expected = TRUE_A + TRUE_B * price + TRUE_C * comp
    qty = np.maximum(0, np.round(expected + rng.normal(0, 6, len(dates)))).astype(int)

    # Unit cost drifts up ~8% over two years
    cost = (22 * (1 + 0.08 * np.arange(len(dates)) / len(dates)) + rng.normal(0, 0.2, len(dates))).round(2)

    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Product": "Classic Mug",
        "Price_Charged": price,
        "Quantity_Sold": qty,
        "Cost_Per_Unit": cost,
        "Competitor_Price": comp.round(2),
        "Flag": np.where(promo, "promo", ""),
    })


def travel_mug(seed=SEED + 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates, months = _days()
    price = _monthly(rng, months, 24, 38)
    month_idx = np.asarray((months - months[0]).map(lambda d: d.n))
    expected = TRAVEL_SCALE * price ** TRAVEL_ELASTICITY * (1 + TRAVEL_GROWTH) ** month_idx
    qty = rng.poisson(expected * rng.lognormal(0, 0.1, len(dates)))
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Product": "Travel Mug",
        "Price_Charged": price,
        "Quantity_Sold": qty,
        "Cost_Per_Unit": _cost(rng, len(dates), 12, 0.05),
        "Competitor_Price": np.nan,  # no competitor tracked for this one
        "Flag": "",
    })


def gift_set(seed=SEED + 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates, months = _days("2023-10-01", END)
    price = _monthly(rng, months, 48, 76)
    comp = _monthly(rng, months, 55, 70) + rng.normal(0, 0.5, len(dates)).round(2)
    season = np.array([GIFT_SEASON.get(m, 1.0) for m in dates.month])
    expected = (GIFT_A + GIFT_B * price + GIFT_C * comp) * season
    qty = np.maximum(0, np.round(expected + rng.normal(0, 4, len(dates)))).astype(int)
    # Sold out on a few December days: sales were capped by stock, not by demand
    stockout = (dates.month == 12) & (dates.day >= 20) & (rng.random(len(dates)) < 0.5)
    qty = np.where(stockout, (qty * 0.3).round(), qty).astype(int)
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Product": "Gift Set",
        "Price_Charged": price,
        "Quantity_Sold": qty,
        "Cost_Per_Unit": _cost(rng, len(dates), 25, 0.06),
        "Competitor_Price": comp.round(2),
        "Flag": np.where(stockout, "stockout", ""),
    })


def new_tumbler(seed=SEED + 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates, months = _days("2026-08-01", END)
    price = _monthly(rng, months, 32, 38)
    qty = np.maximum(0, np.round(70 - 1.2 * price + rng.normal(0, 4, len(dates)))).astype(int)
    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Product": "New Tumbler",
        "Price_Charged": price,
        "Quantity_Sold": qty,
        "Cost_Per_Unit": _cost(rng, len(dates), 14, 0.0),
        "Competitor_Price": np.nan,
        "Flag": "",
    })


def generate() -> pd.DataFrame:
    frames = [classic_mug(), travel_mug(), gift_set(), new_tumbler()]
    return pd.concat(frames, ignore_index=True)[COLUMNS].sort_values(["Date", "Product"], kind="stable")


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "sample_data.csv"
    generate().to_csv(out, index=False)
    print(f"Wrote {out}")
