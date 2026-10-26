"""Pricing Optimization Engine: Streamlit dashboard.

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import io
from dataclasses import asdict
from datetime import date
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import BOOTSTRAP_SAMPLES, COUNTRY_MAP, DEFAULTS, PERIOD_MULT, SEASONAL_MIN_MONTHS
from data_ingestion import PRODUCT, DataValidationError, aggregate, deflate, load_csv
from macro_api import get_fx, get_inflation
from optimizer import ScenarioParams, fit_demand, optimal_price_range, run_scenario
from report import Chart, Series, VLine, build_excel, build_pdf
from translations import LANGUAGES, localize, translate

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "sample_data.csv"

# Categorical slots from the validated reference palette (fixed order), light / dark steps
PALETTE = {
    "light": {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "muted": "#898781", "band": "rgba(137,135,129,0.12)",
              "range": "rgba(42,120,214,0.10)"},
    "dark": {"s1": "#3987e5", "s2": "#d95926", "s3": "#199e70", "muted": "#898781", "band": "rgba(195,194,183,0.10)",
             "range": "rgba(57,135,229,0.16)"},
}

st.set_page_config(page_title="Pricing Optimization Engine", page_icon="📈", layout="wide")


# ---------- cached data access ----------

@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cached_inflation(country: str):
    return get_inflation(country)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def cached_fx(country: str):
    return get_fx(country)


@st.cache_data(show_spinner=False)
def load_rows(raw: bytes, default_cogs: float):
    return load_csv(io.BytesIO(raw), default_cogs)


@st.cache_data(show_spinner=False, max_entries=64)
def cached_range(agg: pd.DataFrame, kind: str, seasonal: bool, params: dict):
    return optimal_price_range(agg, kind, ScenarioParams(**params), seasonal)


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


def reset_shocks(infl, fx):
    st.session_state.shock_infl = float(np.clip(round(infl.value, 1), -10.0, 100.0))
    st.session_state.shock_fx = float(np.clip(round(fx.change_pct or 0.0, 1), -50.0, 100.0))
    st.session_state.shock_comp = 0.0


def macro_badge(v, label: str):
    if v.ok:
        st.badge(f"{label}: {v.source} · {v.as_of or t('badge_live')}", icon=":material/cloud_done:", color="green")
    else:
        st.badge(t("badge_offline", label=label), icon=":material/cloud_off:", color="orange")


# ---------- sidebar ----------

with st.sidebar:
    st.header(t("sidebar_header"))
    upload = st.file_uploader(t("upload_label"), type=["csv", "xlsx"], help=t("upload_help"), key="upload")
    if upload is None:
        st.caption(t("sample_caption"))
        st.download_button(t("sample_download"), SAMPLE_PATH.read_bytes(), "sample_data.csv", "text/csv")
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
    model_kind = st.radio(t("model_label"), ["linear", "loglog"], horizontal=True,
                          format_func=lambda k: t(f"model_{k}"), key="model_kind")
    use_real = st.toggle(t("real_label"), value=True, help=t("real_help"), key="use_real")

# ---------- data ----------

st.title(t("app_title"))
st.caption(t("app_caption", country=t(f"country_{country}"), currency=COUNTRY_MAP[country]["currency"]))

raw = upload.getvalue() if upload is not None else SAMPLE_PATH.read_bytes()
product = None
try:
    rows, data_warnings = load_rows(raw, default_cogs)
    if PRODUCT in rows:
        with product_slot:
            product = st.selectbox(t("product_label"), sorted(rows[PRODUCT].unique()), help=t("product_help"),
                                   key="product")
        rows = rows[rows[PRODUCT] == product].drop(columns=PRODUCT)
    agg, agg_warnings = aggregate(rows)
    data_warnings = data_warnings + agg_warnings
except (DataValidationError, ValueError) as e:
    st.error(t("err_file", error=error_text(e)))
    st.stop()

with st.spinner(t("spinner_macro")):
    infl, fx = cached_inflation(country), cached_fx(country)
    us_infl = infl if country == "US" else cached_inflation("US")

agg, deflate_warnings = deflate(agg, infl.series if use_real else None)
if not use_real:
    deflate_warnings = []

with st.sidebar:
    seasonal = st.toggle(t("season_label"), value=len(agg) >= SEASONAL_MIN_MONTHS,
                         help=t("season_help", min_n=SEASONAL_MIN_MONTHS), key="use_season")

models = {}
for kind in ("linear", "loglog"):
    try:
        models[kind] = fit_demand(agg, kind, seasonal)
    except ValueError as e:
        models[kind] = e
model = models[model_kind]
if isinstance(model, Exception):
    st.error(t("err_model", model=t(f"model_{model_kind}"), error=error_text(model)))
    st.stop()

current_price = float(agg["Price_Charged"].iloc[-1])
base_cogs = cost_override if cost_override > 0 else float(agg["Cost_Per_Unit"].iloc[-1])
base_comp = float(agg["Real_Competitor_Price"].iloc[-1]) if model.has_comp else None

with st.sidebar:
    max_price = st.number_input(t("max_price_label", sym=sym), min_value=0.01,
                                value=float(round(2 * model.p_max, 2)),
                                key=f"max_price_{model_kind}_{product}_{len(agg)}", help=t("max_price_help"))

# Live macro values become the slider defaults, refreshed whenever the country changes
if st.session_state.get("shock_country") != country:
    reset_shocks(infl, fx)
    st.session_state.shock_country = country

metrics_area = st.container()
charts_area = st.container()

# ---------- shock sliders (rendered below the charts) ----------

st.divider()
st.subheader(t("shock_header"))
st.caption(t("shock_caption"))
s1, s2, s3, s4 = st.columns([3, 3, 3, 1.4], vertical_alignment="bottom")
with s1:
    inflation = st.slider(t("shock_infl"), -10.0, 100.0, step=0.5, key="shock_infl", help=t("shock_infl_help"))
with s2:
    fx_shift = st.slider(t("shock_fx"), -50.0, 100.0, step=0.5, key="shock_fx", help=t("shock_fx_help"),
                         disabled=is_usd)
with s3:
    comp_shift = st.slider(t("shock_comp"), -50.0, 50.0, step=1.0, key="shock_comp",
                           disabled=not model.has_comp,
                           help=None if model.has_comp else t("shock_comp_help"))
with s4:
    st.button(t("shock_reset"), on_click=reset_shocks, args=(infl, fx), width="stretch")
passthrough = st.toggle(t("shock_passthrough"), value=True, key="shock_passthrough", help=t("shock_passthrough_help"))
if not model.has_comp:
    st.caption(t("shock_comp_disabled"))

# ---------- scenarios ----------

# Imported inputs are priced in USD, so they inflate at the US rate (for USD countries
# every input is local, so they follow the slider like everything else).
usd_inflation = inflation / 100 if is_usd else us_infl.value / 100

common = dict(base_cogs=base_cogs, fixed_monthly=fixed_monthly, capacity=capacity or np.inf, period=timeframe,
              import_share=import_share / 100, base_comp_price=base_comp, current_price=current_price, max_price=max_price)
scenario = ScenarioParams(**common, inflation=inflation / 100, usd_inflation=usd_inflation,
                          fx_shift=(0 if is_usd else fx_shift) / 100, comp_shift=comp_shift / 100,
                          price_passthrough=passthrough)
result = run_scenario(model, scenario)
today = run_scenario(model, ScenarioParams(**common))
try:
    price_range = cached_range(agg, model_kind, seasonal, asdict(scenario))
except ValueError:
    price_range = None

opt, base = result.optimal, result.baseline

# ---------- metrics ----------

with metrics_area:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric(t("metric_opt_price"), money(opt["price"], sym), t("metric_opt_delta", pct=(opt["price"] / current_price - 1) * 100),
                  help=t("metric_opt_help", price=money(current_price, sym)))
        if price_range:
            st.caption(t("metric_opt_range", low=money(price_range[0], sym), high=money(price_range[1], sym)),
                       help=t("metric_opt_range_help", n=BOOTSTRAP_SAMPLES))
    c2.metric(t("metric_profit", per=per), money(opt["profit"], sym), money(opt["profit"] - base["profit"], sym),
              help=t("metric_profit_help", profit=money(base["profit"], sym)))
    c3.metric(t("metric_ped"), f"{result.ped_opt:.2f}", help=t("metric_ped_help"))
    with c4:
        st.metric(t("metric_r2"), f"{model.r2:.2f}", help=t("metric_r2_help"))
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

    for w in model.warnings + result.warnings:
        st.warning(localize(w, lang), icon=":material/warning:")

# ---------- charts ----------

col = colors()
curve = result.curve
units = t("units")

with charts_area:
    fig = go.Figure()
    cap = curve[curve["cap_binding"]]
    if not cap.empty:
        fig.add_vrect(x0=cap["price"].min(), x1=cap["price"].max(), fillcolor=col["band"], line_width=0,
                      annotation_text=t("chart_capacity"), annotation_position="top left")
    if price_range:
        fig.add_vrect(x0=price_range[0], x1=price_range[1], fillcolor=col["range"], line_width=0,
                      annotation_text=t("chart_range"), annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["profit"], name=t("chart_net_profit"), line=dict(color=col["s1"], width=2.5)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["revenue"], name=t("chart_revenue"), line=dict(color=col["s2"], width=2)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["total_cost"], name=t("chart_total_cost"), line=dict(color=col["s3"], width=2)))
    fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
    fig.add_vline(x=opt["price"], line=dict(color=col["s1"], width=1.5, dash="dot"),
                  annotation_text=t("chart_optimal", price=money(opt["price"], sym)), annotation_position="top right")
    fig.add_vline(x=current_price, line=dict(color=col["muted"], width=1.5, dash="dash"),
                  annotation_text=t("chart_current", price=money(current_price, sym)), annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[opt["price"]], y=[opt["profit"]], mode="markers", name=t("chart_peak"),
                             marker=dict(color=col["s1"], size=11, line=dict(color="white", width=2)),
                             showlegend=False, hoverinfo="skip"))
    for be in result.break_evens:
        fig.add_trace(go.Scatter(x=[be], y=[0], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=col["muted"], size=9, symbol="diamond")))
    style(fig, t("chart_main_title", per=per), t("axis_price", sym=sym), f"{sym} {per}", height=460)
    fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}", selector=dict(mode="lines"))
    st.plotly_chart(fig, width="stretch")
    if result.break_evens:
        st.caption(t("caption_break_even", prices=", ".join(money(b, sym) for b in result.break_evens),
                     cogs=money(result.cogs_final, sym), fixed=money(result.fixed_final, sym), per=per))

    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        price_col = "Real_Price"
        fig.add_trace(go.Scatter(x=agg[price_col], y=agg["Quantity_Sold"] * PERIOD_MULT[timeframe], mode="markers",
                                 name=t("chart_observed"), marker=dict(color=col["s2"], size=9, line=dict(color="white", width=1)),
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
        fig.add_trace(go.Scatter(x=curve["price"], y=today.curve["profit"], name=t("chart_today"),
                                 line=dict(color=col["muted"], width=2, dash="dash")))
        fig.add_trace(go.Scatter(x=curve["price"], y=curve["profit"], name=t("chart_scenario"), line=dict(color=col["s1"], width=2.5)))
        fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
        style(fig, t("chart_shock_title", per=per), t("axis_price", sym=sym), f"{sym} {per}")
        fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}")
        st.plotly_chart(fig, width="stretch")
        d_price = opt["price"] - today.optimal["price"]
        d_profit = opt["profit"] - today.optimal["profit"]
        st.caption(t("caption_shock", d_price=money(d_price, sym), d_profit=money(d_profit, sym), per=per))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg.index, y=agg["Price_Charged"], name=t("chart_your_price"), line=dict(color=col["s1"], width=2)))
    if "Competitor_Price" in agg:
        fig.add_trace(go.Scatter(x=agg.index, y=agg["Competitor_Price"], name=t("chart_comp_price"), line=dict(color=col["s2"], width=2)))
    if use_real and infl.series is not None:
        fig.add_trace(go.Scatter(x=agg.index, y=agg["Real_Price"], name=t("chart_real_price"),
                                 line=dict(color=col["s3"], width=2, dash="dot")))
    style(fig, t("chart_history_title"), "", t("axis_price", sym=sym), height=340)
    fig.update_traces(hovertemplate=f"{sym}%{{y:,.2f}}")
    st.plotly_chart(fig, width="stretch")

# ---------- details ----------

with st.expander(t("details_expander")):
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(f"**{t('details_fitted')}**")
        st.code(model.equation(), language=None)
        columns = [t("col_model"), t("col_r2"), t("col_periods"), t("col_coef")]
        model_rows = []
        for kind, m in models.items():
            fit = (None, None, None) if isinstance(m, Exception) else (round(m.r2, 3), m.n, round(m.b, 3))
            model_rows.append(dict(zip(columns, (t(f"model_{kind}"), *fit))))
        model_table = pd.DataFrame(model_rows)
        st.dataframe(model_table, hide_index=True)
        xed = result.xed_opt
        xed_line = t("details_xed", value=f"{xed:.2f}") if xed is not None else t("details_xed_na")
        st.markdown(f"- {t('details_ped_current', value=f'{result.ped_current:.2f}')}\n- {xed_line}")
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
    st.markdown(f"**{t('details_agg')}**")
    st.dataframe(agg.round(2), width="stretch")

# ---------- export ----------

def on_off(flag: bool) -> str:
    return t("sum_on") if flag else t("sum_off")


summary = ([(t("product_label"), product)] if product else []) + [
    (t("country_label"), f"{t(f'country_{country}')} ({COUNTRY_MAP[country]['currency']})"),
    (t("timeframe_label"), t(f"timeframe_{timeframe}")),
    (t("model_label"), t(f"model_{model_kind}")),
    (t("season_label"), on_off(model.season is not None)),
    (t("real_label"), on_off(use_real)),
    (t("shock_infl"), f"{inflation:.1f}%"),
    (t("shock_fx"), "—" if is_usd else f"{fx_shift:+.1f}%"),
    (t("shock_comp"), f"{comp_shift:+.0f}%" if model.has_comp else "—"),
    (t("shock_passthrough"), on_off(passthrough)),
    (t("sum_current_price"), money(current_price, sym)),
    (t("metric_opt_price"), f"{money(opt['price'], sym)} · {t('metric_opt_delta', pct=(opt['price'] / current_price - 1) * 100)}"),
    (t("sum_range"), f"{money(price_range[0], sym)} – {money(price_range[1], sym)}" if price_range else "—"),
    (t("metric_profit", per=per), money(opt["profit"], sym)),
    (t("sum_profit_current", per=per), money(base["profit"], sym)),
    (t("metric_ped"), f"{result.ped_opt:.2f}"),
    (t("metric_r2"), f"{model.r2:.2f}"),
    (t("sum_unit_cost"), money(result.cogs_final, sym)),
    (t("sum_fixed", per=per), money(result.fixed_final, sym)),
    (t("sum_break_even"), ", ".join(money(b, sym) for b in result.break_evens) or t("sum_none")),
    (t("sum_equation"), model.equation()),
    (t("metric_cpi"), f"{infl.value:.1f}% ({infl.source}, {infl.as_of or '—'})"),
    (t("metric_fx", currency=COUNTRY_MAP[country]["currency"]), f"{fx.value:,.4f} ({fx.source})"),
]
curve_table = curve[["price", "q_demand", "q_sold", "revenue", "total_cost", "profit", "cap_binding"]].rename(columns={
    "price": t("col_price"), "q_demand": t("col_q_demand"), "q_sold": t("col_q_sold"), "revenue": t("chart_revenue"),
    "total_cost": t("chart_total_cost"), "profit": t("chart_net_profit"), "cap_binding": t("col_cap_binding"),
}).round(4)
sheets = {
    t("sheet_summary"): pd.DataFrame(summary, columns=[t("sum_item"), t("sum_value")]),
    t("sheet_curve"): curve_table,
    t("sheet_monthly"): agg.round(4).reset_index(),
    t("sheet_models"): model_table,
}
notes = list(dict.fromkeys(localize(w, lang) for w in
                           model.warnings + result.warnings + data_warnings + deflate_warnings))
chart = Chart(
    title=t("chart_main_title", per=per),
    x=curve["price"].to_numpy(),
    series=[Series(t("chart_net_profit"), curve["profit"].to_numpy(), PALETTE["light"]["s1"], 0.8),
            Series(t("chart_revenue"), curve["revenue"].to_numpy(), PALETTE["light"]["s2"]),
            Series(t("chart_total_cost"), curve["total_cost"].to_numpy(), PALETTE["light"]["s3"])],
    xlabel=t("axis_price", sym=sym),
    vlines=[VLine(opt["price"], t("chart_optimal", price=money(opt["price"], sym)), PALETTE["light"]["s1"]),
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
