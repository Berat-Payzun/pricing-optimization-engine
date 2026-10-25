"""CSV loading, validation, monthly aggregation and CPI deflation."""

from __future__ import annotations

import pandas as pd

from config import MIN_PERIODS_FIT, MIN_PERIODS_WARN

REQUIRED = ["Date", "Price_Charged", "Quantity_Sold"]
OPTIONAL = ["Cost_Per_Unit", "Competitor_Price"]

ALIASES = {
    "date": "Date",
    "price_charged": "Price_Charged",
    "price": "Price_Charged",
    "quantity_sold": "Quantity_Sold",
    "quantity": "Quantity_Sold",
    "qty": "Quantity_Sold",
    "cost_per_unit": "Cost_Per_Unit",
    "cost": "Cost_Per_Unit",
    "cogs": "Cost_Per_Unit",
    "competitor_price": "Competitor_Price",
    "competitor": "Competitor_Price",
}


class DataValidationError(ValueError):
    pass


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        if key in ALIASES:
            rename[col] = ALIASES[key]
    return df.rename(columns=rename)


def load_csv(source, default_cogs: float) -> tuple[pd.DataFrame, list[str]]:
    """Read and clean raw sales rows. Returns (clean_df, warnings)."""
    warnings: list[str] = []
    df = normalize_columns(pd.read_csv(source))

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required column(s): {', '.join(missing)}")

    df = df[[c for c in REQUIRED + OPTIONAL if c in df.columns]].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for col in df.columns.drop("Date"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_raw = len(df)
    df = df.dropna(subset=REQUIRED)
    df = df[(df["Price_Charged"] > 0) & (df["Quantity_Sold"] >= 0)]
    dropped = n_raw - len(df)
    if dropped:
        warnings.append(f"{dropped} of {n_raw} rows dropped (unparseable date, missing or non-positive price, negative quantity).")
    if df.empty:
        raise DataValidationError("No valid rows left after cleaning.")

    df = df.sort_values("Date").reset_index(drop=True)

    if "Cost_Per_Unit" not in df.columns:
        df["Cost_Per_Unit"] = default_cogs
        warnings.append("No Cost_Per_Unit column: using the default COGS for all rows.")
    else:
        n_missing = int(df["Cost_Per_Unit"].isna().sum())
        if n_missing:
            df["Cost_Per_Unit"] = df["Cost_Per_Unit"].fillna(default_cogs)
            warnings.append(f"{n_missing} missing Cost_Per_Unit values filled with the default COGS.")

    if "Competitor_Price" in df.columns:
        df["Competitor_Price"] = df["Competitor_Price"].ffill().bfill()
        if df["Competitor_Price"].isna().all():
            df = df.drop(columns="Competitor_Price")
            warnings.append("Competitor_Price column is empty: competitor effects disabled.")

    return df, warnings


def aggregate(df: pd.DataFrame, freq: str = "MS") -> tuple[pd.DataFrame, list[str]]:
    """Aggregate raw rows to calendar months to smooth out daily/weekly noise.

    Price is quantity-weighted (what customers actually paid on average);
    falls back to a simple mean for periods with zero sales.
    """
    warnings: list[str] = []
    g = df.assign(Revenue=df["Price_Charged"] * df["Quantity_Sold"]).set_index("Date").groupby(pd.Grouper(freq=freq))

    out = pd.DataFrame({"Quantity_Sold": g["Quantity_Sold"].sum()})
    out["Price_Charged"] = (g["Revenue"].sum() / out["Quantity_Sold"]).where(
        out["Quantity_Sold"] > 0, g["Price_Charged"].mean()
    )
    out["Cost_Per_Unit"] = g["Cost_Per_Unit"].mean()
    if "Competitor_Price" in df.columns:
        out["Competitor_Price"] = g["Competitor_Price"].mean()

    out = out.dropna(subset=["Price_Charged"])  # months with no rows at all
    out.index.name = "Date"

    n = len(out)
    if n < MIN_PERIODS_FIT:
        raise DataValidationError(f"Only {n} month(s) of data: at least {MIN_PERIODS_FIT} are needed to fit demand.")
    if n < MIN_PERIODS_WARN:
        warnings.append(f"Only {n} months of data: the demand estimate will be unreliable (6+ recommended).")
    if out["Price_Charged"].nunique() < 2 or out["Price_Charged"].std() < 1e-9:
        raise DataValidationError("Price never varies in the data, so demand response to price cannot be estimated.")
    return out, warnings


def deflate(agg: pd.DataFrame, cpi: pd.Series | None) -> tuple[pd.DataFrame, list[str]]:
    """Add Real_Price / Real_Competitor_Price columns in latest-month money.

    real_price_t = price_t * CPI_latest / CPI_t. Months after the last CPI release
    reuse the latest CPI value (CPI is published with a 1-2 month lag).
    """
    out = agg.copy()
    if cpi is None or cpi.empty:
        out["Real_Price"] = out["Price_Charged"]
        if "Competitor_Price" in out:
            out["Real_Competitor_Price"] = out["Competitor_Price"]
        out["CPI_Factor"] = 1.0
        return out, ["CPI data unavailable: demand fitted on nominal prices."]

    monthly_cpi = cpi.copy()
    monthly_cpi.index = monthly_cpi.index.to_period("M").start_time
    monthly_cpi = monthly_cpi.groupby(level=0).last()
    full_index = monthly_cpi.index.union(out.index)
    aligned = monthly_cpi.reindex(full_index).ffill().bfill().reindex(out.index)

    factor = aligned.iloc[-1] / aligned
    out["CPI_Factor"] = factor.values
    out["Real_Price"] = out["Price_Charged"] * out["CPI_Factor"]
    if "Competitor_Price" in out:
        out["Real_Competitor_Price"] = out["Competitor_Price"] * out["CPI_Factor"]
    return out, []
