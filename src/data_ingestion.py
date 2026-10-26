"""CSV / Excel loading, validation, monthly aggregation and CPI deflation."""

from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import pandas as pd

from config import CPI_STALE_MONTHS, MIN_PERIODS_FIT, MIN_PERIODS_WARN
from translations import Msg

REQUIRED = ["Date", "Price_Charged", "Quantity_Sold"]
OPTIONAL = ["Cost_Per_Unit", "Competitor_Price"]
PRODUCT = "Product"  # optional text column: one file may hold several products

# Header aliases in English, Turkish and German, written in folded form (see fold_header)
ALIASES = {
    "Date": ["date", "tarih", "satis_tarihi", "datum", "verkaufsdatum"],
    "Price_Charged": ["price_charged", "price", "fiyat", "satis_fiyati", "birim_fiyat", "preis", "verkaufspreis"],
    "Quantity_Sold": ["quantity_sold", "quantity", "qty", "adet", "miktar", "satilan_adet", "satis_adedi",
                      "menge", "absatz", "verkaufte_menge", "stuck", "stueck", "stuckzahl", "stueckzahl"],
    "Cost_Per_Unit": ["cost_per_unit", "cost", "cogs", "maliyet", "birim_maliyet", "smm",
                      "kosten", "stuckkosten", "stueckkosten", "einkaufspreis"],
    "Competitor_Price": ["competitor_price", "competitor", "rakip", "rakip_fiyat", "rakip_fiyati",
                         "konkurrenzpreis", "konkurrenz", "wettbewerbspreis"],
    PRODUCT: ["product", "sku", "item", "urun", "urun_adi", "urun_kodu", "produkt", "artikel", "artikelnummer"],
}
ALIAS_LOOKUP = {alias: target for target, aliases in ALIASES.items() for alias in aliases}


class DataValidationError(ValueError):
    pass


def fold_header(name) -> str:
    """'Satış Fiyatı' -> 'satis_fiyati', 'Stückkosten' -> 'stuckkosten', 'Price-Charged' -> 'price_charged'."""
    s = str(name).strip().casefold().replace("ı", "i")
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
    return re.sub(r"[\s\-]+", "_", s)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename, used = {}, set()
    for col in df.columns:
        target = ALIAS_LOOKUP.get(fold_header(col))
        if target and target not in used:
            rename[col] = target
            used.add(target)
    out = df.rename(columns=rename)
    return out.loc[:, ~out.columns.duplicated()]  # if two headers map to one field, the first wins


# Excel in Turkish/German locales saves CSVs with ";" separators, decimal commas
# (1.234,56), dd.mm.yyyy dates and a Windows code page instead of UTF-8.
ENCODINGS = ("utf-8-sig", "cp1254", "cp1252")
DECIMAL_COMMA = r"-?(\d{1,3}(\.\d{3})+|\d+),\d+"
DOTTED_DATE = r"\d{1,2}\.\d{1,2}\.\d{4}.*"


XLSX_MAGIC = b"PK\x03\x04"  # .xlsx files are zip archives


def read_table(source) -> tuple[pd.DataFrame, bool]:
    """Read a CSV or .xlsx file (path, bytes buffer or text buffer) with every column as text.
    Returns (frame, decimal_comma), where decimal_comma says whether "10,5" means 10.5."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    if isinstance(data, bytes) and data.startswith(XLSX_MAGIC):
        # Excel number cells come through as "10.5"; a decimal comma can only be text typed in a cell
        return pd.read_excel(io.BytesIO(data), sheet_name=0, dtype=str), True
    text = data if isinstance(data, str) else decode(data)
    sep = detect_separator(text)
    # With "," as the separator a comma inside a value is a thousands separator (US quoted
    # "1,234"), so decimal commas are only recognised in ";" or tab separated files.
    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str), sep != ","


def decode(data: bytes) -> str:
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
    """Read and clean raw sales rows from a CSV or .xlsx file. Returns (clean_df, warnings)."""
    warnings: list[str] = []
    raw, decimal_comma = read_table(source)
    df = normalize_columns(raw)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataValidationError(Msg("err_missing_cols", cols=", ".join(missing)))

    df = df[[c for c in REQUIRED + OPTIONAL + [PRODUCT] if c in df.columns]].copy()
    df["Date"] = to_dates(df["Date"])
    for col in df.columns.drop(["Date", PRODUCT], errors="ignore"):
        df[col] = to_number(df[col], decimal_comma)
    if PRODUCT in df.columns:
        df[PRODUCT] = df[PRODUCT].fillna("").astype(str).str.strip().replace("", "—")

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
        def fill(s):
            return s.ffill().bfill()

        # Gaps are filled within each product, never from another product's competitor
        df["Competitor_Price"] = (df.groupby(PRODUCT)["Competitor_Price"].transform(fill)
                                  if PRODUCT in df.columns else fill(df["Competitor_Price"]))
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
