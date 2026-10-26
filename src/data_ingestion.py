"""CSV loading, validation, monthly aggregation and CPI deflation."""

from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

from config import CPI_STALE_MONTHS, MIN_PERIODS_FIT, MIN_PERIODS_WARN
from translations import Msg

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


# Excel in Turkish/German locales saves CSVs with ";" separators, decimal commas
# (1.234,56), dd.mm.yyyy dates and a Windows code page instead of UTF-8.
ENCODINGS = ("utf-8-sig", "cp1254", "cp1252")
DECIMAL_COMMA = r"-?(\d{1,3}(\.\d{3})+|\d+),\d+"
DOTTED_DATE = r"\d{1,2}\.\d{1,2}\.\d{4}.*"


def read_text(source) -> str:
    """Return the file's text from a path, a bytes buffer or a text buffer."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    if isinstance(data, str):
        return data
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("cp1252", errors="replace")


def detect_separator(text: str) -> str:
    lines = text.strip().splitlines()
    header = lines[0] if lines else ""
    return max([",", ";", "\t"], key=header.count)


def to_number(values: pd.Series, decimal_comma: bool) -> pd.Series:
    s = values.astype("string").str.strip()
    if decimal_comma:
        is_comma = s.str.fullmatch(DECIMAL_COMMA).fillna(False).astype(bool)
        s = s.where(~is_comma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce").astype("float64")  # plain floats, not nullable Float64


def to_dates(values: pd.Series) -> pd.Series:
    s = values.astype("string").str.strip()
    first = s.dropna()
    dayfirst = not first.empty and bool(re.fullmatch(DOTTED_DATE, first.iloc[0]))
    return pd.to_datetime(s, errors="coerce", dayfirst=dayfirst)


def load_csv(source, default_cogs: float) -> tuple[pd.DataFrame, list[str]]:
    """Read and clean raw sales rows. Returns (clean_df, warnings)."""
    warnings: list[str] = []
    text = read_text(source)
    sep = detect_separator(text)
    df = normalize_columns(pd.read_csv(io.StringIO(text), sep=sep, dtype=str))

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataValidationError(Msg("err_missing_cols", cols=", ".join(missing)))

    df = df[[c for c in REQUIRED + OPTIONAL if c in df.columns]].copy()
    df["Date"] = to_dates(df["Date"])
    # With "," as the separator a comma inside a value is a thousands separator (US quoted
    # "1,234"), so decimal commas are only recognised in ";" or tab separated files.
    for col in df.columns.drop("Date"):
        df[col] = to_number(df[col], decimal_comma=sep != ",")

    n_raw = len(df)
    df = df.dropna(subset=REQUIRED)
    df = df[(df["Price_Charged"] > 0) & (df["Quantity_Sold"] >= 0)]
    dropped = n_raw - len(df)
    if dropped:
        warnings.append(Msg("warn_rows_dropped", dropped=dropped, n_raw=n_raw))
    if df.empty:
        raise DataValidationError(Msg("err_no_valid_rows"))

    df = df.sort_values("Date").reset_index(drop=True)

    if "Cost_Per_Unit" not in df.columns:
        df["Cost_Per_Unit"] = default_cogs
        warnings.append(Msg("warn_no_cost_col"))
    else:
        n_missing = int(df["Cost_Per_Unit"].isna().sum())
        if n_missing:
            df["Cost_Per_Unit"] = df["Cost_Per_Unit"].fillna(default_cogs)
            warnings.append(Msg("warn_cost_filled", n=n_missing))

    if "Competitor_Price" in df.columns:
        df["Competitor_Price"] = df["Competitor_Price"].ffill().bfill()
        if df["Competitor_Price"].isna().all():
            df = df.drop(columns="Competitor_Price")
            warnings.append(Msg("warn_comp_empty"))

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
        raise DataValidationError(Msg("err_too_few_months", n=n, min_n=MIN_PERIODS_FIT))
    if n < MIN_PERIODS_WARN:
        warnings.append(Msg("warn_few_months", n=n, min_n=MIN_PERIODS_WARN))
    if out["Price_Charged"].nunique() < 2 or out["Price_Charged"].std() < 1e-9:
        raise DataValidationError(Msg("err_price_constant"))
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
        return out, [Msg("warn_cpi_unavailable")]

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

    warnings = []
    cpi_end, data_end = monthly_cpi.index.max(), out.index.max()
    if (data_end.year - cpi_end.year) * 12 + data_end.month - cpi_end.month > CPI_STALE_MONTHS:
        warnings.append(Msg("warn_cpi_stale", as_of=cpi_end.strftime("%Y-%m")))
    return out, warnings
