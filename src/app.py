"""Pricing Optimization Engine: Streamlit dashboard.
"""

from __future__ import annotations

import hashlib
import io
import os
import time
from dataclasses import asdict
from datetime import date
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (BOOTSTRAP_SAMPLES, COUNTRY_MAP, DEFAULTS, MAX_CHANGE_DEFAULT, PERIOD_MULT, SEASONAL_MIN_MONTHS,
                    TEST_DEFAULT_STEP, TEST_MAX_WEEKS, TEST_STEP_CHOICES)
from data_ingestion import PRODUCT, DataValidationError, aggregate, deflate, load_csv
from macro_api import FRED_KEY_ENV, fred_api_key, get_fx, get_inflation, uses_fred
from optimizer import (ENDINGS, Guardrails, ScenarioParams, backtest, best_model, bootstrap, competitor_price_at,
                       elasticities, evaluate_test, fit_demand, recommend, run_scenario, sensitivity, step_tradeoff,
                       test_plan)
from portfolio import portfolio, product_inputs
import scenarios
from report import Chart, Series, VLine, build_excel, build_pdf, label_rows
from translations import LANGUAGES, Msg, localize, translate

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "sample_data.csv"

# Categorical slots from the validated reference palette (fixed order), light / dark steps
PALETTE = {
    "light": {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "muted": "#898781", "band": "rgba(137,135,129,0.12)",
              "range": "rgba(42,120,214,0.10)", "label_bg": "rgba(255,255,255,0.85)"},
    "dark": {"s1": "#3987e5", "s2": "#d95926", "s3": "#199e70", "muted": "#898781", "band": "rgba(195,194,183,0.10)",
             "range": "rgba(57,135,229,0.16)", "label_bg": "rgba(14,17,23,0.85)"},
}

st.set_page_config(page_title="Pricing Optimization Engine", page_icon="📈", layout="wide")

# FRED API key: Streamlit secrets (.streamlit/secrets.toml locally, Settings → Secrets on
# Streamlit Cloud) are copied to the environment, where macro_api looks for it.
try:
    if FRED_KEY_ENV in st.secrets:
        os.environ.setdefault(FRED_KEY_ENV, str(st.secrets[FRED_KEY_ENV]))
except Exception:  # no secrets file at all: an environment variable may still be set
    pass


# ---------- cached data access ----------

@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cached_inflation(country: str):
    return get_inflation(country)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cached_fx(country: str):
    return get_fx(country)


OFFLINE_RETRY_S = 600


def live(cached, country: str):
    """A cached macro value, except that an offline fallback is fetched again after 10 minutes
    instead of being kept for the cache's 6 hours."""
    value = cached(country)
    if not value.ok and time.time() - getattr(value, "fetched_at", 0) > OFFLINE_RETRY_S:
        cached.clear(country)
        value = cached(country)
    return value


@st.cache_data(show_spinner=False)
def load_rows(raw: bytes, default_cogs: float, drop_duplicates: bool):
    return load_csv(io.BytesIO(raw), default_cogs, drop_duplicates)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_backtest(agg: pd.DataFrame, kind: str, seasonal: bool, trend: bool):
    return backtest(agg, kind, seasonal, trend=trend)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_bootstrap(agg: pd.DataFrame, kind: str, seasonal: bool, trend: bool, params: dict, ped_price: float):
    return bootstrap(agg, kind, ScenarioParams(**params), seasonal, trend=trend, ped_price=ped_price)


@st.cache_data(show_spinner=False, max_entries=16)
def cached_portfolio(rows: pd.DataFrame, cpi: pd.Series | None, model_choice: str, seasonal: bool, trend: bool,
                     shared: dict, rails: dict):
    return portfolio(rows, cpi, model_choice, seasonal, trend, shared, Guardrails(**rails))


# ---------- language ----------

# Every widget below has an explicit key and uses internal option codes, so switching the
# language (which changes labels and format_func output) never resets the user's inputs.
with st.sidebar:
    lang = st.selectbox("🌐 Language / Dil / Sprache", list(LANGUAGES), format_func=LANGUAGES.get, key="lang")


def t(key: str, **params) -> str:
    return translate(key, lang, **params)


def error_text(e: Exception) -> str:
    return localize(e.args[0] if e.args else e, lang)


# ---------- helpers ----------

def colors() -> dict:
    try:
        mode = "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        mode = "light"
    return PALETTE[mode]


def money(x: float, sym: str) -> str:
    sign = "-" if x < 0 else ""
    return f"{sign}{sym}{abs(x):,.2f}"


def num(x, spec: str = ".2f", suffix: str = "") -> str:
    """A number for display, or "—" when it can't be computed (e.g. elasticity where demand is zero)."""
    return "—" if x is None or not np.isfinite(x) else f"{x:{spec}}{suffix}"


def month_year(ts) -> str:
    return f"{t('months').split(',')[ts.month - 1]} {ts.year}"


def style(fig: go.Figure, title: str, xtitle: str, ytitle: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=15)),
        height=height,
        margin=dict(l=10, r=10, t=60, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
        xaxis=dict(title=xtitle, showgrid=False, zeroline=False),
        yaxis=dict(title=ytitle, zeroline=False),
    )
    return fig


MARKER_PLOT_PX = 600  # assumed plot width when sizing marker labels (narrower than most screens: errs to more rows)
MARKER_CHAR_PX = 6.5  # average character width at 11px
MARKER_ROW = 0.065  # height of one label row, as a fraction of the plot


def add_markers(fig: go.Figure, markers: list[dict], x_lo: float, x_hi: float, bg: str) -> None:
    """Vertical marker lines with their labels at the top. A label sits right of its line (left of
    it near the right edge), and labels that would overlap are stacked in rows instead of drawn on
    top of each other. Each marker: x, text, color, optional dash, width, line (False = label only)."""
    span = max(x_hi - x_lo, 1e-9)
    spans, sides = [], []
    for m in markers:
        w = (len(m["text"]) * MARKER_CHAR_PX + 10) / MARKER_PLOT_PX * span
        right = m["x"] + w <= x_hi
        sides.append(right)
        spans.append((m["x"], m["x"] + w) if right else (m["x"] - w, m["x"]))
    for m in markers:
        if m.get("line", True):
            fig.add_vline(x=m["x"], line=dict(color=m["color"], width=m.get("width", 1.5), dash=m.get("dash", "dot")))
    for m, right, row in zip(markers, sides, label_rows(spans, gap=0.01 * span)):
        fig.add_annotation(x=m["x"], xref="x", y=1 - row * MARKER_ROW, yref="paper", yanchor="top",
                           xanchor="left" if right else "right", xshift=4 if right else -4, showarrow=False,
                           text=m["text"], font=dict(color=m["color"], size=11), bgcolor=bg)


def reset_shocks(infl, fx, us_infl):
    st.session_state.shock_infl = float(np.clip(round(infl.value, 1), -10.0, 100.0))
    st.session_state.shock_usd_infl = float(np.clip(round(us_infl.value, 1), -10.0, 100.0))
    st.session_state.shock_fx = float(np.clip(round(fx.change_pct or 0.0, 1), -50.0, 100.0))
    st.session_state.shock_comp = 0.0


def load_scenario():
    """Uploader callback: runs before the script, so the widgets below draw with the loaded values."""
    upload = st.session_state.get("scenario_upload")
    if upload is None:
        return
    ss = st.session_state
    run_id = ss.get("scenario_status", {}).get("id", 0) + 1
    try:
        loaded = scenarios.load(upload.getvalue())
    except scenarios.ScenarioError as e:
        ss.scenario_status = {"error": e.args[0], "id": run_id}
        return
    for key, value in scenarios.session_updates(loaded, ss.get("country")).items():
        ss[key] = value
    ss.scenario_status = {"loaded": loaded, "id": run_id}


def macro_badge(v, label: str):
    if v.ok:
        st.badge(f"{label}: {v.source} · {v.as_of or t('badge_live')}", icon=":material/cloud_done:", color="green")
    else:
        st.badge(t("badge_offline", label=label), icon=":material/cloud_off:", color="orange")


# ---------- sidebar ----------

with st.sidebar:
    st.header(t("sidebar_header"))
    scenario_box = st.expander(t("scen_header"), icon=":material/save:")
    with scenario_box:
        save_slot = st.empty()  # the save button is added at the end, once every setting is known
        st.file_uploader(t("scen_load"), type=["json"], help=t("scen_load_help"), key="scenario_upload",
                         on_change=load_scenario)
    upload = st.file_uploader(t("upload_label"), type=["csv", "xlsx"], help=t("upload_help"), key="upload")
    if upload is None:
        st.caption(t("sample_caption"))
        st.download_button(t("sample_download"), SAMPLE_PATH.read_bytes(), "sample_data.csv", "text/csv")
    drop_dupes = st.toggle(t("dupes_label"), value=True, help=t("dupes_help"), key="drop_dupes")
    product_slot = st.container()  # filled once the file is read, if it has a product column

    country = st.selectbox(t("country_label"), list(COUNTRY_MAP), format_func=lambda c: t(f"country_{c}"), key="country")
    sym = COUNTRY_MAP[country]["symbol"]
    is_usd = COUNTRY_MAP[country]["currency"] == "USD"  # US and Global: no FX exposure

    timeframe = st.selectbox(t("timeframe_label"), list(PERIOD_MULT), format_func=lambda p: t(f"timeframe_{p}"),
                             help=t("timeframe_help"), key="timeframe")
    per = t(f"per_{timeframe}")
    default_cogs = st.number_input(t("cogs_label", sym=sym), min_value=0.0, value=DEFAULTS["cogs"],
                                   help=t("cogs_help"), key="default_cogs")
    cost_override = st.number_input(t("cost_override_label", sym=sym), min_value=0.0, value=0.0,
                                    help=t("cost_override_help"), key="cost_override")
    fixed_monthly = st.number_input(t("fixed_label", sym=sym), min_value=0.0, value=DEFAULTS["fixed_costs"], step=500.0,
                                    help=t("fixed_help"), key="fixed_monthly")
    capacity = st.number_input(t("capacity_label", per=per), min_value=0,
                               value=0, step=500, help=t("capacity_help"), key="capacity")
    import_share = st.slider(t("import_label"), 0, 100, int(DEFAULTS["import_share"]),
                             help=t("import_help"), key="import_share")
    model_choice = st.radio(t("model_label"), ["auto", "linear", "loglog"], horizontal=True,
                            format_func=lambda k: t(f"model_{k}"), help=t("model_help"), key="model_kind")
    model_note = st.empty()  # which model "auto" picked, once both are fitted
    use_real = st.toggle(t("real_label"), value=True, help=t("real_help"), key="use_real")

# ---------- data ----------

st.title(t("app_title"))
st.caption(t("app_caption", country=t(f"country_{country}"), currency=COUNTRY_MAP[country]["currency"]))

raw = upload.getvalue() if upload is not None else SAMPLE_PATH.read_bytes()
product = all_rows = None
try:
    rows, data_warnings = load_rows(raw, default_cogs, drop_dupes)
    if PRODUCT in rows:
        with product_slot:
            products = sorted(rows[PRODUCT].unique())
            pending = st.session_state.pop("_pending_product", None)
            if pending is not None:
                if pending in products:
                    st.session_state.product = pending
                else:
                    st.session_state.scenario_status["product_missing"] = pending
            product = st.selectbox(t("product_label"), products, help=t("product_help"),
                                   key="product")
        all_rows = rows
        rows = rows[rows[PRODUCT] == product].drop(columns=PRODUCT)
    agg, agg_warnings = aggregate(rows)
    data_warnings = data_warnings + agg_warnings
except (DataValidationError, ValueError) as e:
    st.error(t("err_file", error=error_text(e)))
    st.stop()

data_sha = hashlib.sha256(raw).hexdigest()
scenario_status = st.session_state.get("scenario_status", {})
with scenario_box:
    if "error" in scenario_status:
        st.error(localize(scenario_status["error"], lang))
    elif "loaded" in scenario_status:
        loaded = scenario_status["loaded"]
        st.caption(t("scen_loaded", saved_at=loaded.saved_at[:16].replace("T", " "),
                     file=loaded.data.get("file_name", "—")))
        for w in loaded.warnings:
            st.warning(localize(w, lang))
        if loaded.data.get("sha256") not in (None, data_sha):
            st.warning(t("scen_warn_other_file", file=loaded.data.get("file_name", "—")))
        if "product_missing" in scenario_status:
            st.warning(t("scen_warn_product", product=scenario_status["product_missing"]))

with st.spinner(t("spinner_macro")):
    infl, fx = live(cached_inflation, country), live(cached_fx, country)
    us_infl = infl if country == "US" else live(cached_inflation, "US")

agg, deflate_warnings = deflate(agg, infl.series if use_real else None)
if not use_real:
    deflate_warnings = []
if fred_api_key() is None and uses_fred(country):
    deflate_warnings.append(Msg("warn_fred_no_key"))

with st.sidebar:
    seasonal = st.toggle(t("season_label"), value=len(agg) >= SEASONAL_MIN_MONTHS,
                         help=t("season_help", min_n=SEASONAL_MIN_MONTHS), key="use_season")
    use_trend = st.toggle(t("trend_label"), value=False, help=t("trend_help"), key="use_trend")

models = {}
for kind in ("linear", "loglog"):
    try:
        models[kind] = fit_demand(agg, kind, seasonal, use_trend)
    except ValueError as e:
        models[kind] = e
backtests = {kind: None if isinstance(m, Exception) else cached_backtest(agg, kind, seasonal, use_trend)
             for kind, m in models.items()}
model_kind = best_model(models, backtests) if model_choice == "auto" else model_choice
if model_kind is None:  # neither model could be fitted: report the linear fit's reason
    model_kind = "linear"
elif model_choice == "auto":
    model_note.caption(t("model_auto_caption", model=t(f"model_{model_kind}"),
                         wape=num(backtests[model_kind].wape * 100, ".1f", "%") if backtests[model_kind] else "—"))
bt = backtests[model_kind]
model = models[model_kind]
if isinstance(model, Exception):
    st.error(t("err_model", model=t(f"model_{model_kind}"), error=error_text(model)))
    st.stop()

# Months mostly flagged as stockout/promo stay in the charts but not in the fit, and a promo
# month's price is never "current"
excluded = agg["Excluded"].astype(bool) if "Excluded" in agg else pd.Series(False, index=agg.index)
# In the model's money (the last month's), which differs from the nominal price only when the last month is excluded
current_price, latest_cogs, base_comp = product_inputs(agg, model)
base_cogs = cost_override if cost_override > 0 else latest_cogs

with st.sidebar:
    max_price_key = f"max_price_{model_kind}_{product}_{len(agg)}"
    if "_pending_max_price" in st.session_state:
        st.session_state[max_price_key] = st.session_state.pop("_pending_max_price")
    max_price = st.number_input(t("max_price_label", sym=sym), min_value=0.01,
                                value=float(round(2 * model.p_max, 2)),
                                key=max_price_key, help=t("max_price_help"))

    st.subheader(t("fees_header"))
    fee_pct = st.number_input(t("fee_label"), 0.0, 90.0, 0.0, step=0.5, help=t("fee_help"), key="variable_fees")
    prices_incl_vat = st.toggle(t("vat_toggle"), value=False, help=t("vat_toggle_help"), key="prices_incl_vat")
    # Keyed by country so the prefilled rate follows the country selection
    vat_rate = st.number_input(t("vat_label"), 0.0, 50.0, float(COUNTRY_MAP[country]["vat"]), step=0.5,
                               help=t("vat_help"), key=f"vat_{country}", disabled=not prices_incl_vat)
    extra_cost = st.number_input(t("extra_cost_label", sym=sym), min_value=0.0, value=0.0, help=t("extra_cost_help"),
                                 key="extra_unit_cost")

    st.subheader(t("rails_header"))
    max_change = st.number_input(t("max_change_label"), 0.0, 100.0, MAX_CHANGE_DEFAULT, step=1.0,
                                 help=t("max_change_help"), key="max_change")
    min_margin = st.number_input(t("min_margin_label"), 0.0, 95.0, 0.0, step=1.0, help=t("min_margin_help"),
                                 key="min_margin")
    f1, f2 = st.columns(2)
    price_floor = f1.number_input(t("floor_label", sym=sym), min_value=0.0, value=0.0, help=t("floor_ceiling_help"),
                                  key="price_floor")
    price_ceiling = f2.number_input(t("ceiling_label", sym=sym), min_value=0.0, value=0.0,
                                    help=t("floor_ceiling_help"), key="price_ceiling")
    ending = st.selectbox(t("ending_label"), ENDINGS, format_func=lambda e: t(f"ending_{e.lstrip('.')}"),
                          help=t("ending_help"), key="ending")

    st.subheader(t("reaction_header"))
    match_cut = st.slider(t("match_cut_label"), 0, 100, 0, step=5, format="%d%%", help=t("match_cut_help"),
                          key="comp_match_cut", disabled=not model.has_comp)
    match_rise = st.slider(t("match_rise_label"), 0, 100, 0, step=5, format="%d%%", help=t("match_rise_help"),
                           key="comp_match_rise", disabled=not model.has_comp)
    if not model.has_comp:
        st.caption(t("reaction_disabled"))
        match_cut = match_rise = 0

# Live macro values become the slider defaults, refreshed whenever the country changes
if st.session_state.get("shock_country") != country:
    reset_shocks(infl, fx, us_infl)
    st.session_state.shock_country = country

metrics_area = st.container()
charts_area = st.container()

# ---------- shock sliders (rendered below the charts) ----------

st.divider()
st.subheader(t("shock_header"))
st.caption(t("shock_caption"))
s1, s5, s2, s3, s4 = st.columns([3, 3, 3, 3, 1.4], vertical_alignment="bottom")
with s1:
    inflation = st.slider(t("shock_infl"), -10.0, 100.0, step=0.5, key="shock_infl", help=t("shock_infl_help"))
with s5:
    # Imported inputs are priced in USD, so they inflate at the US rate. For USD countries every
    # input is local and follows the inflation slider.
    usd_infl_pct = st.slider(t("shock_usd_infl"), -10.0, 100.0, step=0.5, key="shock_usd_infl", disabled=is_usd,
                             help=t("shock_usd_infl_help", source=us_infl.source, as_of=us_infl.as_of or "—"))
with s2:
    fx_shift = st.slider(t("shock_fx"), -50.0, 100.0, step=0.5, key="shock_fx", help=t("shock_fx_help"),
                         disabled=is_usd)
with s3:
    comp_shift = st.slider(t("shock_comp"), -50.0, 50.0, step=1.0, key="shock_comp",
                           disabled=not model.has_comp,
                           help=None if model.has_comp else t("shock_comp_help"))
with s4:
    st.button(t("shock_reset"), on_click=reset_shocks, args=(infl, fx, us_infl), width="stretch")
passthrough = st.toggle(t("shock_passthrough"), value=True, key="shock_passthrough", help=t("shock_passthrough_help"))
if not model.has_comp:
    st.caption(t("shock_comp_disabled"))

# ---------- scenarios ----------

usd_inflation = (inflation if is_usd else usd_infl_pct) / 100

common = dict(base_cogs=base_cogs, fixed_monthly=fixed_monthly, capacity=capacity or np.inf, period=timeframe,
              import_share=import_share / 100, base_comp_price=base_comp, current_price=current_price, max_price=max_price,
              fee_rate=fee_pct / 100,
              vat=vat_rate / 100 if prices_incl_vat else 0.0, extra_unit_cost=extra_cost,
              comp_match_cut=match_cut / 100, comp_match_rise=match_rise / 100)
# Headline: today's costs and price level, no shock. Scenario: the sliders, 12 months out.
today_params = ScenarioParams(**common)
today = run_scenario(model, today_params)
scenario = ScenarioParams(**common, inflation=inflation / 100, usd_inflation=usd_inflation,
                          fx_shift=(0 if is_usd else fx_shift) / 100, comp_shift=comp_shift / 100,
                          price_passthrough=passthrough)
result = run_scenario(model, scenario)
rails = Guardrails(max_change=max_change / 100, min_margin=min_margin / 100, floor=price_floor,
                   ceiling=price_ceiling, ending=ending)
rec = recommend(model, today_params, today, rails)
no_reaction = None  # the same recommendation if the competitor didn't react, for comparison
if match_cut or match_rise:
    still = ScenarioParams(**{**common, "comp_match_cut": 0.0, "comp_match_rise": 0.0})
    no_reaction = recommend(model, still, run_scenario(model, still), rails)
# The bootstrap range is for the unconstrained optimum: shown only when the recommendation is that
# optimum, and never when there is no optimum inside the price range
try:
    boot = cached_bootstrap(agg, model_kind, seasonal, use_trend, asdict(today_params), rec.price)
except ValueError:
    boot = None
price_range = boot.price if boot is not None and today.interior and not rec.binding else None

opt, rec_row = result.optimal, rec.row
unconstrained = today.optimal["price"]
ped_rec, xed_rec = elasticities(model, rec.price, competitor_price_at(model, today_params, rec.price))
money_month = month_year(agg.index.max())  # the demand model's prices are in this month's money
scenario_month = month_year(agg.index.max() + pd.DateOffset(months=12))
limits = ", ".join(t(f"limit_{b}") for b in rec.binding)

# Per-unit split of the recommended price (today's costs)
breakdown = [
    ("breakdown_price", rec.price),
    ("breakdown_vat", -(rec.price - rec.price / (1 + today_params.vat))),
    ("breakdown_fees", -today_params.fee_rate * rec.price),
    ("breakdown_cogs", -(today.cogs_final - extra_cost)),
    ("breakdown_extra", -extra_cost),
]
breakdown = breakdown[:1] + [(k, v) for k, v in breakdown[1:] if abs(v) > 1e-12]
unit_margin = sum(v for _, v in breakdown)

# ---------- metrics ----------

with metrics_area:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric(t("metric_rec_price"), money(rec.price, sym),
                  t("metric_opt_delta", pct=(rec.price / current_price - 1) * 100),
                  help=t("metric_rec_help", month=money_month, price=money(current_price, sym)))
        if rec.binding:
            st.caption(t("caption_unconstrained", price=money(unconstrained, sym), limits=limits))
        elif abs(rec.price - unconstrained) >= 0.005:
            st.caption(t("caption_unrounded", price=money(unconstrained, sym)))
        if no_reaction is not None:
            st.caption(t("caption_no_reaction", price=money(no_reaction.price, sym)))
        if price_range:
            st.caption(t("metric_opt_range", low=money(price_range[0], sym), high=money(price_range[1], sym)),
                       help=t("metric_opt_range_help", n=BOOTSTRAP_SAMPLES))
    c2.metric(t("metric_profit", per=per), money(rec_row["profit"], sym),
              money(rec_row["profit"] - today.baseline["profit"], sym),
              help=t("metric_profit_help", profit=money(today.baseline["profit"], sym)))
    with c3:
        st.metric(t("metric_ped"), num(ped_rec), help=t("metric_ped_help"))
        if boot is not None and boot.ped is not None:
            st.caption(t("metric_ped_ci", low=num(boot.ped[0]), high=num(boot.ped[1])),
                       help=t("metric_ped_ci_help", n=BOOTSTRAP_SAMPLES))
            conf = boot.ped_confidence
            st.badge(t(f"badge_conf_{conf}"), color={"high": "green", "medium": "orange", "low": "red"}[conf],
                     icon=":material/insights:")
    with c4:
        if bt is not None:
            # Out-of-sample forecast error replaces the flattering in-sample R²
            st.metric(t("metric_backtest"), num(bt.wape * 100, ".1f", "%"), help=t("metric_backtest_help", n=len(bt.months)))
            naive = num(bt.naive_wape * 100, ".1f", "%")
            if bt.beats_naive and bt.wape < 0.15:
                st.badge(t("badge_bt_good", naive=naive), icon=":material/check_circle:", color="green")
            elif bt.beats_naive and bt.wape < 0.30:
                st.badge(t("badge_bt_ok", naive=naive), icon=":material/info:", color="orange")
            else:
                st.badge(t("badge_bt_poor", naive=naive), icon=":material/warning:", color="red")
        else:
            st.metric(t("metric_r2"), f"{model.r2:.2f}", help=t("metric_r2_help"))
            st.caption(t("caption_r2_insample"))
        if model.kind == "loglog" and model.n_dropped:
            st.badge(t("badge_periods_dropped", n_dropped=model.n_dropped, total=model.n + model.n_dropped),
                     icon=":material/warning:", color="orange")
    with c5:
        st.metric(t("metric_cpi"), f"{infl.value:.1f}%")
        macro_badge(infl, t("badge_cpi"))
    with c6:
        st.metric(t("metric_fx", currency=COUNTRY_MAP[country]["currency"]), f"{fx.value:,.4f}",
                  t("metric_fx_delta", pct=fx.change_pct) if fx.change_pct is not None and not is_usd else None,
                  delta_color="inverse")
        macro_badge(fx, t("badge_fx"))

    if not today.interior:
        st.error(t("err_no_interior", max=money(max_price, sym)), icon=":material/block:")
    for w in dict.fromkeys(model.warnings + today.warnings + rec.warnings):
        st.warning(localize(w, lang), icon=":material/warning:")

col = colors()
units = t("units")

with metrics_area, st.expander(t("breakdown_expander")):
    b1, b2 = st.columns([3, 2])
    labels = [t(k) for k, _ in breakdown] + [t("breakdown_margin")]
    values = [v for _, v in breakdown] + [unit_margin]
    with b1:
        fig = go.Figure(go.Waterfall(
            x=labels, y=values, measure=["absolute"] + ["relative"] * (len(breakdown) - 1) + ["total"],
            text=[money(v, sym) for v in values], textposition="outside",
            increasing=dict(marker=dict(color=col["s1"])), decreasing=dict(marker=dict(color=col["s2"])),
            totals=dict(marker=dict(color=col["s3"] if unit_margin >= 0 else col["s2"])),
            connector=dict(line=dict(color=col["muted"], width=1)), hoverinfo="skip"))
        style(fig, t("breakdown_title", price=money(rec.price, sym)), "", sym, height=340)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with b2:
        breakdown_table = pd.DataFrame({
            t("col_item"): labels,
            t("col_per_unit"): [money(v, sym) for v in values],
            t("col_share"): [f"{v / rec.price * 100:.1f}%" for v in values],
        })
        st.dataframe(breakdown_table, hide_index=True, width="stretch")
        st.caption(t("breakdown_caption", units=f"{rec_row['q_sold']:,.0f}", per=per,
                     contribution=money(unit_margin * rec_row["q_sold"], sym), fixed=money(today.fixed_final, sym),
                     profit=money(rec_row["profit"], sym)))

# ---------- sensitivity (tornado) ----------

sens = sensitivity(model, today_params) if today.interior else None
with metrics_area, st.expander(t("sens_expander"), icon=":material/tune:"):
    if sens is None or sens.empty:
        st.caption(t("sens_na"))
    else:
        base_price = sens.attrs["base_price"]
        names = [t(f"sens_factor_{f}") for f in sens["factor"]][::-1]  # biggest at the top
        fig = go.Figure()
        for side, color in (("low", col["s2"]), ("high", col["s1"])):
            fig.add_trace(go.Bar(
                y=names, x=(sens[f"price_{side}"] - base_price).to_numpy()[::-1], orientation="h",
                name=t(f"sens_{side}"), marker_color=color,
                customdata=np.stack([sens[f"price_{side}"], sens[f"profit_{side}"]], axis=1)[::-1],
                hovertemplate=sym + "%{customdata[0]:,.2f} · " + t("sens_profit") + " " + sym
                + "%{customdata[1]:,.0f}<extra></extra>"))
        style(fig, t("sens_title", price=money(base_price, sym)), t("sens_axis", sym=sym), "", height=300)
        fig.update_layout(barmode="overlay")
        fig.add_vline(x=0, line=dict(color=col["muted"], width=1))
        st.plotly_chart(fig, width="stretch")
        st.caption(t("sens_caption"))

# ---------- portfolio (files with several products) ----------

pf = None
if all_rows is not None:
    shared = dict(period=timeframe, import_share=import_share / 100, fee_rate=fee_pct / 100,
                  vat=today_params.vat, extra_unit_cost=extra_cost,
                  comp_match_cut=match_cut / 100, comp_match_rise=match_rise / 100)
    pf_rails = dict(max_change=max_change / 100, min_margin=min_margin / 100, ending=ending)
    with st.spinner(t("pf_spinner")):
        pf = cached_portfolio(all_rows, infl.series if use_real else None, model_choice, seasonal, use_trend,
                              shared, pf_rails)
    pf_view = pd.DataFrame({
        t("pf_col_product"): pf["product"],
        t("pf_col_model"): [t(f"model_{k}") if isinstance(k, str) else "—" for k in pf["model"]],
        t("pf_col_current"): [money(v, sym) if pd.notna(v) else "—" for v in pf["current_price"]],
        t("pf_col_rec"): [money(v, sym) if pd.notna(v) else "—" for v in pf["rec_price"]],
        t("pf_col_change"): [num(v * 100, "+.1f", "%") for v in pf["change"]],
        t("pf_col_ped"): [num(v) for v in pf["ped"]],
        t("pf_col_uplift", per=per): [money(v, sym) if pd.notna(v) else "—" for v in pf["uplift"]],
        t("pf_col_wape"): [num(v * 100, ".1f", "%") for v in pf["wape"]],
        t("pf_col_status"): [t("pf_status_ok") if s == "ok" else t("pf_status_no_optimum") if s == "no_optimum"
                             else localize(e, lang) for s, e in zip(pf["status"], pf["error"])],
    })
    with metrics_area, st.expander(t("pf_expander", n=len(pf)), icon=":material/inventory_2:"):
        st.caption(t("pf_caption", per=per))
        st.dataframe(pf_view, hide_index=True, width="stretch")

# ---------- charts ----------

curve = today.curve

with charts_area:
    fig = go.Figure()
    cap = curve[curve["cap_binding"]]
    markers = []
    if not cap.empty:
        fig.add_vrect(x0=cap["price"].min(), x1=cap["price"].max(), fillcolor=col["band"], line_width=0)
        markers.append(dict(x=float(cap["price"].min()), text=t("chart_capacity"), color=col["muted"], line=False))
    if price_range:
        fig.add_vrect(x0=price_range[0], x1=price_range[1], fillcolor=col["range"], line_width=0,
                      annotation_text=t("chart_range"), annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["profit"], name=t("chart_net_profit"), line=dict(color=col["s1"], width=3)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["revenue"], name=t("chart_revenue"), line=dict(color=col["s2"], width=1.5)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["total_cost"], name=t("chart_total_cost"), line=dict(color=col["s3"], width=1.5)))
    fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
    markers.append(dict(x=rec.price, text=t("chart_recommended", price=money(rec.price, sym)), color=col["s1"]))
    if abs(rec.price - unconstrained) >= 0.005:
        markers.append(dict(x=unconstrained, text=t("chart_unconstrained", price=money(unconstrained, sym)),
                            color=col["muted"], width=1))
    markers.append(dict(x=current_price, text=t("chart_current", price=money(current_price, sym)),
                        color=col["muted"], dash="dash"))
    add_markers(fig, markers, float(curve["price"].min()), float(curve["price"].max()), col["label_bg"])
    fig.add_trace(go.Scatter(x=[rec.price], y=[rec_row["profit"]], mode="markers", name=t("chart_peak"),
                             marker=dict(color=col["s1"], size=11, line=dict(color="white", width=2)),
                             showlegend=False, hoverinfo="skip"))
    for be in today.break_evens:
        fig.add_trace(go.Scatter(x=[be], y=[0], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=col["muted"], size=9, symbol="diamond")))
    style(fig, t("chart_main_title", per=per), t("axis_price", sym=sym), f"{sym} {per}", height=460)
    fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}", selector=dict(mode="lines"))
    st.plotly_chart(fig, width="stretch")
    if today.break_evens:
        st.caption(t("caption_break_even", prices=", ".join(money(b, sym) for b in today.break_evens),
                     cogs=money(today.cogs_final, sym), fixed=money(today.fixed_final, sym), per=per))

    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        price_col = "Real_Price"
        fit_months, out_months = agg[~excluded], agg[excluded]
        fig.add_trace(go.Scatter(x=fit_months[price_col], y=fit_months["Quantity_Sold"] * PERIOD_MULT[timeframe],
                                 mode="markers", name=t("chart_observed"),
                                 marker=dict(color=col["s2"], size=9, line=dict(color="white", width=1)),
                                 hovertemplate=f"{sym}%{{x:,.2f}} → %{{y:,.0f}} {units}<extra></extra>"))
        if not out_months.empty:
            fig.add_trace(go.Scatter(x=out_months[price_col], y=out_months["Quantity_Sold"] * PERIOD_MULT[timeframe],
                                     mode="markers", name=t("chart_excluded"),
                                     marker=dict(color="rgba(0,0,0,0)", size=9, line=dict(color=col["muted"], width=1.5)),
                                     hovertemplate=f"{sym}%{{x:,.2f}} → %{{y:,.0f}} {units}<extra></extra>"))
        # Fitted demand in today's money (no shock), comparable with the observed real prices
        fig.add_trace(go.Scatter(x=today.curve["price"], y=today.curve["q_demand"], name=t("chart_fitted"), line=dict(color=col["s1"], width=2),
                                 hovertemplate=f"%{{y:,.0f}} {units}<extra></extra>"))
        style(fig, t("chart_demand_title", per=per),
              t("axis_price_kind", sym=sym, kind=t("price_real" if use_real else "price_nominal")), t("axis_units"))
        fig.update_layout(hovermode="closest")
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=agg.index, y=agg["Price_Charged"], name=t("chart_your_price"), line=dict(color=col["s1"], width=2)))
        if "Competitor_Price" in agg:
            fig.add_trace(go.Scatter(x=agg.index, y=agg["Competitor_Price"], name=t("chart_comp_price"), line=dict(color=col["s2"], width=2)))
        if use_real and infl.series is not None:
            fig.add_trace(go.Scatter(x=agg.index, y=agg["Real_Price"], name=t("chart_real_price"),
                                     line=dict(color=col["s3"], width=2, dash="dot")))
        style(fig, t("chart_history_title"), "", t("axis_price", sym=sym))
        fig.update_traces(hovertemplate=f"{sym}%{{y:,.2f}}")
        st.plotly_chart(fig, width="stretch")

# ---------- scenario results (below the sliders) ----------

sc1, sc2, sc3 = st.columns(3)
sc1.metric(t("scenario_opt_label", month=scenario_month), money(opt["price"], sym),
           t("scenario_opt_delta", pct=(opt["price"] / rec.price - 1) * 100),
           help=t("scenario_opt_help", month=scenario_month))
sc2.metric(t("scenario_profit_label", per=per), money(opt["profit"], sym))
sc3.metric(t("scenario_cogs_label"), money(result.cogs_final, sym))
st.caption(t("scenario_no_rails"))
for w in result.warnings:
    st.warning(localize(w, lang), icon=":material/warning:")

fig = go.Figure()
# Each run has its own price grid, so each line is drawn against its own prices
fig.add_trace(go.Scatter(x=today.curve["price"], y=today.curve["profit"], name=t("chart_today"),
                         line=dict(color=col["muted"], width=2, dash="dash")))
fig.add_trace(go.Scatter(x=result.curve["price"], y=result.curve["profit"], name=t("chart_scenario"),
                         line=dict(color=col["s1"], width=2.5)))
fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
style(fig, t("chart_shock_title", per=per), t("axis_price", sym=sym), f"{sym} {per}")
fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}")
st.plotly_chart(fig, width="stretch")
st.caption(t("caption_shock", d_price=money(opt["price"] - unconstrained, sym),
             d_profit=money(opt["profit"] - today.optimal["profit"], sym), per=per))

# ---------- price test plan ----------

st.divider()
st.subheader(t("test_header"))
st.caption(t("test_caption"))
# Conservative noise: the larger of the in-sample residual SD and the backtest's forecast error
noise_month = max(model.resid_sd, bt.rmse if bt else 0.0)
tp1, tp2 = st.columns([1, 2])
with tp1:
    test_step = st.slider(t("test_step_label"), 1.0, 30.0, TEST_DEFAULT_STEP * 100, step=0.5, format="%.1f%%",
                          help=t("test_step_help"), key="test_step")
plan = test_plan(model, today_params, unconstrained, noise_month, rails, test_step / 100)
tradeoff = step_tradeoff(model, today_params, unconstrained, noise_month, rails,
                         TEST_STEP_CHOICES + (test_step / 100,))
with tp1:
    needed = plan.weeks_needed
    st.metric(t("test_weeks_metric"), f"{needed:,.0f}" if np.isfinite(needed) else "∞",
              help=t("test_weeks_help", max_weeks=TEST_MAX_WEEKS))
    st.caption(t("test_noise_caption", sd=f"{plan.sd_week:,.0f}", diff=f"{abs(plan.diff):,.0f}", units=units))
with tp2:
    # Weeks fall roughly with the square of the step: a bigger step stands out from weekly noise sooner
    shown = tradeoff[np.isfinite(tradeoff["weeks_needed"])]
    fig = go.Figure(go.Bar(
        x=[f"{s_ * 100:g}%" for s_ in shown["step"]], y=shown["weeks_needed"],
        marker_color=[col["s1"] if abs(s_ - test_step / 100) < 1e-9 else
                      (col["s3"] if w_ <= TEST_MAX_WEEKS else col["muted"])
                      for s_, w_ in zip(shown["step"], shown["weeks_needed"])],
        text=[f"{w_:,.0f}" for w_ in shown["weeks_needed"]], textposition="outside",
        customdata=shown["test_price"], hovertemplate=f"{sym}%{{customdata:,.2f}}: %{{y:,.0f}}<extra></extra>"))
    fig.add_hline(y=TEST_MAX_WEEKS, line=dict(color=col["muted"], width=1, dash="dash"),
                  annotation_text=t("test_chart_max", weeks=TEST_MAX_WEEKS), annotation_position="top right")
    style(fig, t("test_chart_title"), t("test_chart_x"), t("test_chart_y"), height=300)
    fig.update_layout(showlegend=False, xaxis=dict(type="category"),
                      yaxis=dict(type="log", title=t("test_chart_y")))
    st.plotly_chart(fig, width="stretch")
    st.caption(t("test_chart_caption"))
st.markdown(t("test_summary", weeks=plan.weeks, half=plan.weeks // 2, test=money(plan.test_price, sym),
              current=money(current_price, sym), exp_test=f"{plan.expected_test:,.0f}",
              exp_current=f"{plan.expected_current:,.0f}", units=units))
for w in plan.warnings:
    st.warning(localize(w, lang), icon=":material/warning:")
plan_columns = {"week": t("col_week"), "arm": t("col_arm"), "price": t("col_price"), "expected": t("col_expected"),
                "low": t("col_low"), "high": t("col_high")}
plan_table = (plan.schedule.assign(arm=plan.schedule["arm"].map({"test": t("arm_test"), "current": t("arm_current")}))
              .rename(columns=plan_columns).round(2))
plan_table[t("col_actual")] = None
# A loaded scenario's actual units come back only if it is the same test (prices and length)
saved_plan = scenario_status["loaded"].test_plan if "loaded" in scenario_status else None
restored = scenarios.plan_matches(saved_plan, plan.test_price, current_price, plan.weeks)
if restored:
    plan_table[t("col_actual")] = saved_plan["actual"]
    st.caption(t("scen_plan_restored", n=sum(a is not None for a in saved_plan["actual"])))
elif saved_plan is not None:
    st.caption(t("scen_plan_changed"))
edited = st.data_editor(
    plan_table, hide_index=True, width="stretch", disabled=list(plan_columns.values()),
    column_config={t("col_actual"): st.column_config.NumberColumn(min_value=0.0, step=1.0)},
    # A new plan (product, model or prices changed) starts with an empty Actual column
    key=f"test_plan_{product}_{model_kind}_{plan.test_price:.2f}_{current_price:.2f}_{plan.weeks}"
        f"_{scenario_status.get('id', 0) if restored else 0}",
)
test_result = evaluate_test(plan, edited[t("col_actual")])
if test_result is None:
    st.caption(t("test_need_more"))
else:
    text = t(f"test_verdict_{test_result.code}", observed=f"{test_result.observed_diff:+,.0f}",
             expected=f"{plan.diff:+,.0f}", low=f"{test_result.ci[0]:+,.0f}", high=f"{test_result.ci[1]:+,.0f}",
             e_obs=f"{test_result.elasticity_observed:.2f}", e_model=f"{test_result.elasticity_model:.2f}")
    (st.success if test_result.code == "consistent" else st.warning)(text)
    if abs(test_result.level_ratio - 1) > 0.2:
        st.info(t("test_level_shift", pct=(test_result.level_ratio - 1) * 100))
st.caption(t("test_not_saved"))

# ---------- details ----------

with st.expander(t("details_expander")):
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"**{t('details_fitted')}**")
        st.code(model.equation(), language=None)
        columns = [t("col_model"), t("col_backtest"), t("col_naive"), t("col_r2"), t("col_periods"), t("col_coef")]
        model_rows = []
        for kind, m in models.items():
            b = backtests[kind]
            errors = (num(b.wape * 100, ".1f", "%"), num(b.naive_wape * 100, ".1f", "%")) if b is not None else ("—", "—")
            fit = (None, None, None) if isinstance(m, Exception) else (round(m.r2, 3), m.n, round(m.b, 3))
            model_rows.append(dict(zip(columns, (t(f"model_{kind}"), *errors, *fit))))
        model_table = pd.DataFrame(model_rows)
        st.dataframe(model_table, hide_index=True)
        xed_line = t("details_xed", value=num(xed_rec)) if xed_rec is not None else t("details_xed_na")
        st.markdown(f"- {t('details_ped_current', value=num(today.ped_current))}\n- {xed_line}")
        st.markdown(f"- {t('details_price_range', low=money(model.p_min, sym), high=money(model.p_max, sym))}")
    with m2:
        st.markdown(f"**{t('details_notes')}**")
        notes = data_warnings + deflate_warnings + model.warnings
        if notes:
            for n in notes:
                st.markdown(f"- {localize(n, lang)}")
        else:
            st.markdown(f"- {t('details_no_issues')}")
        st.markdown(f"- {t('details_months', n=len(agg), start=month_year(agg.index.min()), end=month_year(agg.index.max()))}")
    if bt is not None:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bt.months, y=bt.actual, name=t("chart_actual"), mode="lines+markers",
                                 line=dict(color=col["s2"], width=2)))
        fig.add_trace(go.Scatter(x=bt.months, y=bt.forecast, name=t("chart_forecast"), mode="lines+markers",
                                 line=dict(color=col["s1"], width=2)))
        fig.add_trace(go.Scatter(x=bt.months, y=bt.naive, name=t("chart_naive"),
                                 line=dict(color=col["muted"], width=1.5, dash="dash")))
        style(fig, t("chart_backtest_title", n=len(bt.months)), "", t("axis_units"), height=320)
        fig.update_traces(hovertemplate=f"%{{y:,.0f}} {units}")
        st.plotly_chart(fig, width="stretch")
    st.markdown(f"**{t('details_agg')}**")
    st.dataframe(agg.round(2), width="stretch")

# ---------- export ----------

def on_off(flag: bool) -> str:
    return t("sum_on") if flag else t("sum_off")


vat_text = t("vat_included", rate=vat_rate) if prices_incl_vat else t("vat_excluded")
per_unit = " · ".join(f"{t(k)} {money(v, sym)}" for k, v in breakdown[1:])
summary = ([(t("product_label"), product)] if product else []) + [
    (t("country_label"), f"{t(f'country_{country}')} ({COUNTRY_MAP[country]['currency']})"),
    (t("timeframe_label"), t(f"timeframe_{timeframe}")),
    (t("model_label"), t(f"model_{model_kind}")),
    (t("season_label"), on_off(model.season is not None)),
    (t("trend_label"), on_off(model.trend is not None)),
    (t("real_label"), on_off(use_real)),
    (t("sum_current_price"), money(current_price, sym)),
    (t("metric_rec_price"), f"{money(rec.price, sym)} · {t('metric_opt_delta', pct=(rec.price / current_price - 1) * 100)}"),
    (t("sum_unconstrained"), money(unconstrained, sym)),
    (t("sum_limits"), limits or t("sum_none")),
    (t("sum_range"), f"{money(price_range[0], sym)} – {money(price_range[1], sym)}" if price_range else "—"),
    (t("metric_profit", per=per), money(rec_row["profit"], sym)),
    (t("sum_profit_current", per=per), money(today.baseline["profit"], sym)),
    (t("metric_ped"), num(ped_rec)),
    (t("sum_ped_ci"), f"{num(boot.ped[0])} – {num(boot.ped[1])} ({t(f'badge_conf_{boot.ped_confidence}')})"
     if boot is not None and boot.ped is not None else "—"),
    (t("metric_backtest"), t("sum_backtest_value", wape=bt.wape * 100, naive=bt.naive_wape * 100, n=len(bt.months))
     if bt is not None and np.isfinite(bt.wape) and np.isfinite(bt.naive_wape) else "—"),
    (t("metric_r2"), f"{model.r2:.2f}"),
    (t("sum_guardrails"), t("sum_guardrails_value", max_change=max_change, min_margin=min_margin,
                            floor=money(price_floor, sym) if price_floor else "—",
                            ceiling=money(price_ceiling, sym) if price_ceiling else "—",
                            ending=t(f"ending_{ending.lstrip('.')}"))),
    (t("sum_fees"), t("sum_fees_value", fees=fee_pct, vat=vat_text,
                      extra=money(extra_cost, sym))),
    (t("reaction_header"), t("sum_reaction_value", cut=match_cut, rise=match_rise)
     + (f" · {t('caption_no_reaction', price=money(no_reaction.price, sym))}" if no_reaction else "")),
    (t("sum_per_unit"), f"{per_unit} · {t('breakdown_margin')} {money(unit_margin, sym)} "
                        f"({unit_margin / rec.price * 100:.1f}%)"),
    (t("sum_unit_cost"), money(today.cogs_final, sym)),
    (t("sum_fixed", per=per), money(today.fixed_final, sym)),
    (t("sum_break_even"), ", ".join(money(b, sym) for b in today.break_evens) or t("sum_none")),
    (t("sum_equation"), model.equation()),
    (t("sum_test_plan"), t("sum_test_plan_value", test=money(plan.test_price, sym), weeks=plan.weeks,
                           diff=f"{plan.diff:+,.0f}")),
    (t("sum_scenario"), scenario_month),
    (t("shock_infl"), f"{inflation:.1f}%"),
    (t("shock_usd_infl"), "—" if is_usd else f"{usd_infl_pct:.1f}%"),
    (t("shock_fx"), "—" if is_usd else f"{fx_shift:+.1f}%"),
    (t("shock_comp"), f"{comp_shift:+.0f}%" if model.has_comp else "—"),
    (t("shock_passthrough"), on_off(passthrough)),
    (t("scenario_opt_label", month=scenario_month), money(opt["price"], sym)),
    (t("scenario_profit_label", per=per), money(opt["profit"], sym)),
    (t("scenario_cogs_label"), money(result.cogs_final, sym)),
    (t("metric_cpi"), f"{infl.value:.1f}% ({infl.source}, {infl.as_of or '—'})"),
    (t("metric_fx", currency=COUNTRY_MAP[country]["currency"]), f"{fx.value:,.4f} ({fx.source})"),
]
curve_columns = {
    "price": t("col_price"), "q_demand": t("col_q_demand"), "q_sold": t("col_q_sold"), "revenue": t("chart_revenue"),
    "vat": t("col_vat"), "fees": t("col_fees"), "total_cost": t("chart_total_cost"), "profit": t("chart_net_profit"),
    "margin_pct": t("col_margin"), "cap_binding": t("col_cap_binding"),
}


def curve_table(c: pd.DataFrame) -> pd.DataFrame:
    return c.assign(margin_pct=c["margin_pct"] * 100)[list(curve_columns)].rename(columns=curve_columns).round(4)


sheets = {
    t("sheet_summary"): pd.DataFrame(summary, columns=[t("sum_item"), t("sum_value")]),
    t("sheet_curve"): curve_table(today.curve),
    t("sheet_scenario_curve"): curve_table(result.curve),
    t("sheet_monthly"): agg.round(4).reset_index(),
    t("sheet_models"): model_table,
    t("sheet_test_plan"): plan_table,  # Actual column left empty to fill in during the test
    **({t("sheet_portfolio"): pf_view} if pf is not None else {}),
    **({t("sheet_sensitivity"): pd.DataFrame({
        t("sens_col_factor"): [t(f"sens_factor_{f}") for f in sens["factor"]],
        t("sens_col_price_low"): sens["price_low"].round(2), t("sens_col_price_high"): sens["price_high"].round(2),
        t("sens_col_profit_low"): sens["profit_low"].round(2), t("sens_col_profit_high"): sens["profit_high"].round(2),
    })} if sens is not None and not sens.empty else {}),
    **({t("sheet_backtest"): pd.DataFrame({t("col_month"): bt.months.strftime("%Y-%m"), t("chart_actual"): bt.actual,
                                           t("chart_forecast"): bt.forecast, t("chart_naive"): bt.naive}).round(2)}
       if bt is not None else {}),
}
notes = ([] if today.interior else [t("err_no_interior", max=money(max_price, sym))]) + list(dict.fromkeys(
    localize(w, lang) for w in model.warnings + today.warnings + rec.warnings + result.warnings + data_warnings
    + deflate_warnings))
chart = Chart(
    title=t("chart_main_title", per=per),
    x=curve["price"].to_numpy(),
    series=[Series(t("chart_net_profit"), curve["profit"].to_numpy(), PALETTE["light"]["s1"], 0.8),
            Series(t("chart_revenue"), curve["revenue"].to_numpy(), PALETTE["light"]["s2"]),
            Series(t("chart_total_cost"), curve["total_cost"].to_numpy(), PALETTE["light"]["s3"])],
    xlabel=t("axis_price", sym=sym),
    vlines=[VLine(rec.price, t("chart_recommended", price=money(rec.price, sym)), PALETTE["light"]["s1"]),
            VLine(current_price, t("chart_current", price=money(current_price, sym)), PALETTE["light"]["muted"], dashed=True)],
    band=(price_range[0], price_range[1], t("chart_range")) if price_range else None,
)
title = t("app_title") + (f" · {product}" if product else "")
subtitle = t("app_caption", country=t(f"country_{country}"), currency=COUNTRY_MAP[country]["currency"])
stem = "pricing_" + "".join(ch if ch.isalnum() else "_" for ch in str(product or "results")) + f"_{date.today():%Y-%m-%d}"

st.divider()
st.subheader(t("export_header"))
st.caption(t("export_caption"))
e1, e2, _ = st.columns([1, 1, 2])
# The files are built only when a button is clicked (callable data, run on another thread),
# so sliders stay fast. partial() binds this run's values, not whatever a later rerun holds.
e1.download_button(t("export_excel"), data=partial(build_excel, sheets), file_name=f"{stem}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   on_click="ignore", width="stretch", icon=":material/table_view:")
e2.download_button(t("export_pdf"), data=partial(build_pdf, title, subtitle, summary, chart, t("pdf_notes"), notes,
                                                 t("pdf_footer", date=f"{date.today():%Y-%m-%d}")),
                   file_name=f"{stem}.pdf", mime="application/pdf",
                   on_click="ignore", width="stretch", icon=":material/picture_as_pdf:")

st.divider()
# Required by the FRED API terms of use (kept in English, as worded by the St. Louis Fed)
st.caption("This product uses the FRED® API but is not endorsed or certified by the Federal Reserve Bank of St. Louis.")

# ---------- save scenario (drawn in the sidebar's scenario box) ----------

actual_units = pd.to_numeric(edited[t("col_actual")], errors="coerce")
current_settings = dict(
    drop_dupes=drop_dupes, country=country, timeframe=timeframe, default_cogs=default_cogs,
    cost_override=cost_override, fixed_monthly=fixed_monthly, capacity=capacity, import_share=import_share,
    model_kind=model_choice, use_real=use_real, use_season=seasonal, use_trend=use_trend, product=product, max_price=max_price,
    variable_fees=fee_pct, prices_incl_vat=prices_incl_vat, vat_rate=vat_rate,
    extra_unit_cost=extra_cost, max_change=max_change, min_margin=min_margin, price_floor=price_floor,
    price_ceiling=price_ceiling, ending=ending,
    # The sliders' own values: match_cut/rise are forced to 0 when the data has no competitor column
    comp_match_cut=st.session_state.get("comp_match_cut", 0), comp_match_rise=st.session_state.get("comp_match_rise", 0),
    shock_infl=inflation, shock_usd_infl=usd_infl_pct, shock_fx=fx_shift, shock_comp=comp_shift, shock_passthrough=passthrough, test_step=test_step,
)
saved_test = ({"test_price": plan.test_price, "current_price": current_price, "weeks": plan.weeks,
               "actual": [None if pd.isna(a) else float(a) for a in actual_units]}
              if actual_units.notna().any() else None)
data_meta = {"sha256": data_sha, "file_name": upload.name if upload is not None else SAMPLE_PATH.name,
             "product": product}
save_slot.download_button(t("scen_save"), data=partial(scenarios.dump, current_settings, saved_test, data_meta),
                          file_name=f"scenario_{stem.removeprefix('pricing_')}.json", mime="application/json",
                          on_click="ignore", width="stretch", icon=":material/download:", help=t("scen_save_help"))
