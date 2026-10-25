"""Generate sample_data.csv: 24 months of daily sales with a known demand curve.

True daily demand:  Q = 120 - 2.0 * Price + 1.0 * Competitor_Price + noise
Prices are set once a month (with occasional weekend promos), so the monthly
aggregates span a wide enough price range to identify the slope.

Usage:  python scripts/generate_sample_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

TRUE_A, TRUE_B, TRUE_C = 120.0, -2.0, 1.0
SEED = 42


def generate(start="2024-10-01", end="2026-09-30", seed=SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    months = dates.to_period("M")
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
        "Price_Charged": price,
        "Quantity_Sold": qty,
        "Cost_Per_Unit": cost,
        "Competitor_Price": comp.round(2),
    })


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "sample_data.csv"
    generate().to_csv(out, index=False)
    print(f"Wrote {out}")
