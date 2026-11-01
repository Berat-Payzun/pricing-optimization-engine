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
# Flag headers that often hold something else, like a transaction status or a free-text note. In such
# a column only the flag words count (other values are ordinary rows, without a warning), "Sale" is
# an ordinary transaction rather than a promo, and a column with no flag words at all is ignored.
GENERIC_FLAG_HEADERS = set(ALIASES[FLAG]) - {"flag", "flags"}
GENERIC_NOT_FLAGS = {"sale"}
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
THOUSANDS_COMMA = r"-?\d{1,3}(,\d{3})+(\.\d+)?"  # US style: 1,234 or 1,234.56
AMBIGUOUS_COMMA = r"-?\d{1,3},\d{3}"  # 1,250 is 1250 in the US and 1.25 in Turkey or Germany
ISO_DATE = r"\d{4}-\d{1,2}-\d{1,2}"
# A UTC offset after a time ("2024-02-05T10:00:00+01:00", "...Z"): dropped, keeping the local time
# of the sale, so every date lands in one time-zone-free column
UTC_OFFSET = r"^(.*\d:\d{2}(?::\d{2}(?:\.\d+)?)?)\s*(?:Z|UTC|[+-]\d{2}(?::?\d{2})?)$"
# dd.mm.yyyy, dd/mm/yy, mm/dd/yyyy, dd-mm-yyyy ...: first field, separator, second field, year, rest (a time)
NUMERIC_DATE = r"^(\d{1,2})([./-])(\d{1,2})\2(\d{4}|\d{2})(?!\d)(.*)$"

XLSX_MAGIC = b"PK\x03\x04"  # .xlsx files are zip archives
# What kind of file read_table read; it sets how "1,250" is read when nothing else settles it
CSV_COMMA, CSV_OTHER, XLSX = "csv_comma", "csv_other", "xlsx"


def read_table(source) -> tuple[pd.DataFrame, str]:
    """Read a CSV or .xlsx file (path, bytes buffer or text buffer) with every column as text.
    Returns (frame, kind): CSV_COMMA, CSV_OTHER (";" or tab separated) or XLSX."""
    data = Path(source).read_bytes() if isinstance(source, (str, Path)) else source.read()
    if isinstance(data, bytes) and data.startswith(XLSX_MAGIC):
        return pd.read_excel(io.BytesIO(data), sheet_name=0, dtype=str), XLSX
    text = data if isinstance(data, str) else decode(data)
    sep = detect_separator(text)
    return pd.read_csv(io.StringIO(text), sep=sep, dtype=str), CSV_COMMA if sep == "," else CSV_OTHER


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


def _comma_kinds(s: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Masks of (stripped text) values that can only be a decimal comma (1.234,56; 12,5), only a
    thousands comma (1,234.56; 1,234,567), and values that could be either (1,250)."""
    def match(pattern):
        return s.str.fullmatch(pattern).fillna(False).astype(bool)

    ambiguous = match(AMBIGUOUS_COMMA)
    return match(DECIMAL_COMMA) & ~ambiguous, match(THOUSANDS_COMMA) & ~ambiguous, ambiguous


def resolve_decimal_comma(kinds: list[tuple[pd.Series, pd.Series, pd.Series]], hint: bool | None,
                          explicit: bool, file_kind: str) -> tuple[bool, bool]:
    """How to read ambiguous values like "1,250", from the _comma_kinds masks of the numeric columns:
    1. the format most of the unambiguous values use;
    2. an `explicit` hint (a file format the user picked);
    3. a comma-separated CSV: thousands comma (a decimal comma there would split the value, so
       commas inside values are US quoting like "1,234"; Turkish/German Excel uses ";");
    4. the hint (the country's convention);
    5. ";" or tab separated CSV: decimal comma; .xlsx: decimal point.
    Returns (decimal_comma, hint_decided), hint_decided meaning step 4 settled values in the file."""
    n_dec = sum(int(d.sum()) for d, _, _ in kinds)
    n_thou = sum(int(t.sum()) for _, t, _ in kinds)
    if n_dec or n_thou:
        return n_dec > n_thou, False
    if hint is not None and explicit:
        return hint, False
    if file_kind == CSV_COMMA:
        return False, False
    if hint is not None:
        return hint, any(bool(a.any()) for _, _, a in kinds)
    return file_kind == CSV_OTHER, False


def to_number(values: pd.Series, decimal_comma: bool, kinds=None) -> pd.Series:
    """Text to numbers. A value that can only be read one way is read that way; `decimal_comma`
    decides only the ambiguous ones, so a file mixing 1,234.50 and 12,5 keeps both. `kinds`: the
    column's _comma_kinds masks, when already computed."""
    s = values.astype("string").str.strip()
    decimal, thousands, ambiguous = kinds if kinds is not None else _comma_kinds(s)
    decimal = decimal | (ambiguous & decimal_comma)
    thousands = thousands | (ambiguous & (not decimal_comma))
    s = s.where(~decimal, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    s = s.where(~thousands, s.str.replace(",", "", regex=False))
    return pd.to_numeric(s, errors="coerce").astype("float64")  # plain floats, not nullable Float64


def date_parts(values: pd.Series) -> tuple[pd.Series, pd.DataFrame]:
    """(stripped text, NUMERIC_DATE fields per value), shared by date_order and to_dates."""
    s = values.astype("string").str.strip()
    return s, s.str.extract(NUMERIC_DATE)


def date_order(parts: pd.DataFrame, hint: bool | None, explicit: bool = False) -> tuple[bool, bool]:
    """Whether numeric dates like 05/02/2024 are day first, from date_parts' fields. The data decides
    when any value settles it (a first field above 12: day first; a second field above 12: month
    first), dotted dates are always day first, and otherwise `hint` (the user's file format or the
    country) decides, else month first. Returns (dayfirst, hint_decided); hint_decided is never set
    for an `explicit` hint, which the user chose knowingly."""
    parts = parts.dropna(subset=[0])
    if parts.empty:
        return False, False
    first, second = parts[0].astype(int), parts[2].astype(int)
    if (first > 12).any():
        return True, False
    if (second > 12).any():
        return False, False
    if (parts[1] == ".").any():
        return True, False
    return (hint, not explicit) if hint is not None else (False, False)


def _parse(text: pd.Series) -> pd.Series:
    """ISO-style text (year first) to time-zone-free timestamps: ISO 8601 where it fits, else
    pandas' per-value guess, which also reads times like "1:30 PM"."""
    text = text.str.replace(UTC_OFFSET, r"\1", regex=True)
    out = pd.to_datetime(text, format="ISO8601", errors="coerce")
    bad = out.isna() & text.notna()
    if bad.any():
        out = out.astype("datetime64[ns]")
        out[bad] = pd.to_datetime(text[bad], format="mixed", errors="coerce")
    return out


def to_dates(values: pd.Series, dayfirst: bool = False, parts: pd.DataFrame | None = None) -> pd.Series:
    """Parse dates value by value, so a column mixing ISO (2024-02-05) and numeric (05/02/24) dates
    reads both: ISO as year-month-day, numeric dates in the `dayfirst` order (a 2-digit year is
    20yy), anything else ("Feb 5, 2024") by pandas' own guess. A time after the date is kept
    (also "1:30 PM"); a UTC offset is dropped, keeping the local time. `parts`: from date_parts."""
    s, parts = date_parts(values) if parts is None else (values.astype("string").str.strip(), parts)
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    iso = s.str.match(ISO_DATE).fillna(False).astype(bool)
    numeric = parts[0].notna() & ~iso
    other = s.notna() & ~iso & ~numeric
    if iso.any():
        out[iso] = _parse(s[iso])
    if numeric.any():
        p = parts[numeric]
        day, month = (p[0], p[2]) if dayfirst else (p[2], p[0])
        year = p[3].where(p[3].str.len() == 4, "20" + p[3])
        out[numeric] = _parse(year + "-" + month.str.zfill(2) + "-" + day.str.zfill(2) + p[4].fillna(""))
    if other.any():
        out[other] = pd.to_datetime(s[other].str.replace(UTC_OFFSET, r"\1", regex=True), format="mixed",
                                    errors="coerce")
    return out


def load_csv(source, default_cogs: float, drop_duplicates: bool = True, dayfirst: bool | None = None,
             decimal_comma: bool | None = None, explicit: bool = False) -> tuple[pd.DataFrame, list[str]]:
    """Read and clean raw sales rows from a CSV or .xlsx file. Returns (clean_df, warnings).

    Exact duplicate rows usually come from combining overlapping exports and would double
    the sales; `drop_duplicates=False` keeps them for transaction logs where they can be real.
    `dayfirst` and `decimal_comma` say how to read dates like 05/02/2024 and numbers like 1,250
    when the data itself leaves them ambiguous (None: month first, and the file type's default).
    `explicit` says the user picked them as the file's format: they then also override a
    comma-separated file's thousands comma, and no "read as ..." warning is added."""
    warnings: list[str] = []
    raw, file_kind = read_table(source)
    df = normalize_columns(raw)
    flag_header = next((c for c in raw.columns if ALIAS_LOOKUP.get(fold_header(c)) == FLAG), None)

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise DataValidationError(Msg("err_missing_cols", cols=", ".join(missing)))

    df = df[[c for c in REQUIRED + OPTIONAL + [PRODUCT, FLAG] if c in df.columns]].copy()
    _, parts = date_parts(df["Date"])
    order, by_hint = date_order(parts, dayfirst, explicit)
    if by_hint:
        warnings.append(Msg("warn_dates_dmy") if order else Msg("warn_dates_mdy"))
    df["Date"] = to_dates(df["Date"], order, parts)
    numeric = list(df.columns.drop(["Date", PRODUCT, FLAG], errors="ignore"))
    text = {col: df[col].astype("string").str.strip() for col in numeric}
    kinds = {col: _comma_kinds(s) for col, s in text.items()}
    comma, by_hint = resolve_decimal_comma(list(kinds.values()), decimal_comma, explicit, file_kind)
    if by_hint:
        warnings.append(Msg("warn_numbers_comma") if comma else Msg("warn_numbers_point"))
    for col in numeric:
        number = to_number(text[col], comma, kinds[col])
        # "inf" parses as a number, and 1e308 overflows the monthly sums: neither is a real price or
        # quantity, so both count as missing (rows missing a required value are dropped and counted)
        df[col] = number.where(np.isfinite(number) & (number.abs() < MAX_VALUE))
    if PRODUCT in df.columns:
        df[PRODUCT] = df[PRODUCT].fillna("").astype(str).str.strip().replace("", "—")
    if FLAG in df.columns:
        folded = df[FLAG].fillna("").map(fold_header)
        generic = fold_header(flag_header) in GENERIC_FLAG_HEADERS
        lookup = {k: v for k, v in FLAG_LOOKUP.items() if not (generic and k in GENERIC_NOT_FLAGS)}
        flags = folded.map(lookup).fillna("")  # unknown values count as clean
        if generic and not (flags != "").any():
            if (folded != "").any():
                warnings.append(Msg("warn_flag_col_ignored", column=str(flag_header)))
            df = df.drop(columns=FLAG)
        else:
            unknown = sorted(set(folded[(folded != "") & (flags == "")]))
            if unknown and not generic:
                warnings.append(Msg("warn_flag_unknown", values=", ".join(unknown[:5])))
            df[FLAG] = flags

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
