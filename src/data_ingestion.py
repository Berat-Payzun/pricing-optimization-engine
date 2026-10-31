"""CSV / Excel loading, validation, monthly aggregation and CPI deflation."""

from __future__ import annotations

import io
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from config import CPI_STALE_MONTHS, MIN_PERIODS_FIT, MIN_PERIODS_WARN
from translations import Msg

REQUIRED = ["Date", "Price_Charged", "Quantity_Sold"]
OPTIONAL = ["Cost_Per_Unit", "Competitor_Price"]
PRODUCT = "Product"  # optional text column: one file may hold several products
FLAG = "Flag"  # optional text column marking stockout / promo rows, left out of the demand fit
MAX_VALUE = 1e15  # larger numbers are no real price, cost or quantity (₺1 quadrillion); treated as missing

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
    FLAG: ["flag", "flags", "status", "note", "durum", "etiket", "isaret", "kennzeichen", "hinweis", "markierung"],
}
ALIAS_LOOKUP = {alias: target for target, aliases in ALIASES.items() for alias in aliases}

# Flag values in English, Turkish and German (folded form), mapped to "stockout" or "promo"
FLAG_VALUES = {
    "stockout": ["stockout", "stock_out", "out_of_stock", "oos", "stok_yok", "stokta_yok", "tukendi",
                 "ausverkauft", "nicht_vorratig", "nicht_vorraetig", "fehlbestand"],
    "promo": ["promo", "promotion", "sale", "discount", "campaign", "kampanya", "indirim",
              "aktion", "rabatt", "angebot"],
}
FLAG_LOOKUP = {alias: flag for flag, aliases in FLAG_VALUES.items() for alias in aliases}
# A month with more than this share of flagged days is left out of the fit entirely
FLAG_EXCLUDE_SHARE = 0.5


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


def load_csv(source, default_cogs: float, drop_duplicates: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Read and clean raw sales rows from a CSV or .xlsx file. Returns (clean_df, warnings).

    Exact duplicate rows usually come from combining overlapping exports and would double
    the sales; `drop_duplicates=False` keeps them for transaction logs where they can be real."""
    warnings: list[str] = []
    raw, decimal_comma = read_table(source)
    df = normalize_columns(raw)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataValidationError(Msg("err_missing_cols", cols=", ".join(missing)))

    df = df[[c for c in REQUIRED + OPTIONAL + [PRODUCT, FLAG] if c in df.columns]].copy()
    df["Date"] = to_dates(df["Date"])
    for col in df.columns.drop(["Date", PRODUCT, FLAG], errors="ignore"):
        number = to_number(df[col], decimal_comma)
        # "inf" parses as a number, and 1e308 overflows the monthly sums: neither is a real price or
        # quantity, so both count as missing (rows missing a required value are dropped and counted)
        df[col] = number.where(np.isfinite(number) & (number.abs() < MAX_VALUE))
    if PRODUCT in df.columns:
        df[PRODUCT] = df[PRODUCT].fillna("").astype(str).str.strip().replace("", "—")
    if FLAG in df.columns:
        folded = df[FLAG].fillna("").map(fold_header)
        unknown = sorted(set(folded[(folded != "") & ~folded.isin(list(FLAG_LOOKUP))]))
        if unknown:
            warnings.append(Msg("warn_flag_unknown", values=", ".join(unknown[:5])))
        df[FLAG] = folded.map(FLAG_LOOKUP).fillna("")  # unknown values count as clean

    n_raw = len(df)
    df = df.dropna(subset=REQUIRED)
    df = df[(df["Price_Charged"] > 0) & (df["Quantity_Sold"] >= 0)]
    dropped = n_raw - len(df)
    if dropped:
        warnings.append(Msg("warn_rows_dropped", dropped=dropped, n_raw=n_raw))
    if df.empty:
        raise DataValidationError(Msg("err_no_valid_rows"))

    n_dup = int(df.duplicated().sum())
    if n_dup and drop_duplicates:
        df = df.drop_duplicates()
        warnings.append(Msg("warn_duplicates_dropped", n=n_dup))
    elif n_dup:
        warnings.append(Msg("warn_duplicates_kept", n=n_dup))

    df = df.sort_values("Date").reset_index(drop=True)

    if "Cost_Per_Unit" not in df.columns:
        df["Cost_Per_Unit"] = default_cogs
        warnings.append(Msg("warn_no_cost_col"))
    else:
        negative = df["Cost_Per_Unit"] < 0  # a typo or a credit note, never a unit cost
        if negative.any():
            df.loc[negative, "Cost_Per_Unit"] = float("nan")
            warnings.append(Msg("warn_cost_negative", n=int(negative.sum())))
        n_missing = int(df["Cost_Per_Unit"].isna().sum())
        if n_missing:
            df["Cost_Per_Unit"] = df["Cost_Per_Unit"].fillna(default_cogs)
            warnings.append(Msg("warn_cost_filled", n=n_missing))
    n_loss = int((df["Cost_Per_Unit"] > df["Price_Charged"]).sum())
    if n_loss:  # can be real (loss leaders, clearance), but is often a unit mix-up
        warnings.append(Msg("warn_cost_above_price", n=n_loss, n_raw=len(df)))

    if "Competitor_Price" in df.columns:
        nonpositive = df["Competitor_Price"] <= 0
        if nonpositive.any():  # treated as missing and filled like any other gap
            df.loc[nonpositive, "Competitor_Price"] = float("nan")
            warnings.append(Msg("warn_comp_nonpositive", n=int(nonpositive.sum())))

        def fill(s):
            return s.ffill().bfill()

        # Gaps are filled within each product, never from another product's competitor
        df["Competitor_Price"] = (df.groupby(PRODUCT)["Competitor_Price"].transform(fill)
                                  if PRODUCT in df.columns else fill(df["Competitor_Price"]))
        if df["Competitor_Price"].isna().all():
            df = df.drop(columns="Competitor_Price")
            warnings.append(Msg("warn_comp_empty"))

    return df, warnings


def _monthly(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Price is quantity-weighted (what customers actually paid on average);
    falls back to a simple mean for periods with zero sales."""
    g = df.assign(Revenue=df["Price_Charged"] * df["Quantity_Sold"]).set_index("Date").groupby(pd.Grouper(freq=freq))
    out = pd.DataFrame({"Quantity_Sold": g["Quantity_Sold"].sum()})
    out["Price_Charged"] = (g["Revenue"].sum() / out["Quantity_Sold"]).where(
        out["Quantity_Sold"] > 0, g["Price_Charged"].mean()
    )
    out["Cost_Per_Unit"] = g["Cost_Per_Unit"].mean()
    if "Competitor_Price" in df.columns:
        out["Competitor_Price"] = g["Competitor_Price"].mean()
    return out


def _days(df: pd.DataFrame, freq: str) -> pd.Series:
    """Distinct calendar days with rows, per month (so transaction-level files count days, not rows)."""
    return df.assign(Day=df["Date"].dt.normalize()).set_index("Date").groupby(pd.Grouper(freq=freq))["Day"].nunique()


def aggregate(df: pd.DataFrame, freq: str = "MS") -> tuple[pd.DataFrame, list[str]]:
    """Aggregate raw rows to calendar months to smooth out daily/weekly noise.

    With a Flag column, days with a stockout or promo row are left out: sales from a month's
    clean days are scaled up to all its days, and a month that is mostly flagged is kept for
    the charts but marked Excluded from the demand fit.
    """
    warnings: list[str] = []
    if "Competitor_Price" in df.columns and df["Competitor_Price"].isna().all():
        # In a file with several products, only some may come with competitor prices
        df = df.drop(columns="Competitor_Price")
        warnings.append(Msg("warn_comp_empty"))
    out = _monthly(df, freq).dropna(subset=["Price_Charged"])  # months with no rows at all
    out.index.name = "Date"

    flagged = df[FLAG] != "" if FLAG in df.columns else pd.Series(False, index=df.index)
    if flagged.any():
        day = df["Date"].dt.normalize()
        clean_rows = ~day.isin(day[flagged])
        n_days = _days(df, freq).reindex(out.index)
        clean_days = _days(df[clean_rows], freq).reindex(out.index).fillna(0)
        share = 1 - clean_days / n_days
        excluded = share > FLAG_EXCLUDE_SHARE
        scaled = (share > 0) & ~excluded
        clean = _monthly(df[clean_rows], freq).reindex(out.index)
        out.loc[scaled] = clean.loc[scaled]
        out.loc[scaled, "Quantity_Sold"] *= (n_days / clean_days)[scaled]
        out["Flagged_Share"] = share
        out["Excluded"] = excluded
        if scaled.any():
            warnings.append(Msg("warn_flag_scaled", n=int(scaled.sum())))
        if excluded.any():
            months = df["Date"].dt.to_period("M").dt.start_time
            has_stockout = (df[FLAG] == "stockout").groupby(months).any().reindex(out.index, fill_value=False)
            n_stockout = int((excluded & has_stockout).sum())
            warnings.append(Msg("warn_flag_excluded", n=int(excluded.sum()), stockout=n_stockout,
                                promo=int(excluded.sum()) - n_stockout))

    fit = out[~out["Excluded"]] if "Excluded" in out else out
    n = len(fit)
    if n < MIN_PERIODS_FIT:
        raise DataValidationError(Msg("err_too_few_months", n=n, min_n=MIN_PERIODS_FIT))
    if n < MIN_PERIODS_WARN:
        warnings.append(Msg("warn_few_months", n=n, min_n=MIN_PERIODS_WARN))
    if fit["Quantity_Sold"].sum() <= 0:
        raise DataValidationError(Msg("err_no_sales"))
    if fit["Price_Charged"].nunique() < 2 or fit["Price_Charged"].std() < 1e-9:
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
