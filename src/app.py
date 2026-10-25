"""Pricing Optimization Engine: Streamlit dashboard.

Run with:  streamlit run src/app.py
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import COUNTRY_MAP, DEFAULTS, PERIOD_MULT
from data_ingestion import DataValidationError, aggregate, deflate, load_csv
from macro_api import get_fx, get_inflation
from optimizer import ScenarioParams, fit_demand, run_scenario

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "sample_data.csv"
PERIOD_LABEL = {"Monthly": "per month", "Quarterly": "per quarter", "Annual": "per year"}

# Categorical slots from the validated reference palette (fixed order), light / dark steps
PALETTE = {
    "light": {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "muted": "#898781", "band": "rgba(137,135,129,0.12)"},
    "dark": {"s1": "#3987e5", "s2": "#d95926", "s3": "#199e70", "muted": "#898781", "band": "rgba(195,194,183,0.10)"},
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
def load_data(raw: bytes, default_cogs: float):
    df, warnings = load_csv(io.BytesIO(raw), default_cogs)
    agg, agg_warnings = aggregate(df)
    return agg, warnings + agg_warnings


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
        st.badge(f"{label}: {v.source} · {v.as_of or 'live'}", icon=":material/cloud_done:", color="green")
    else:
        st.badge(f"{label}: offline, using manual default", icon=":material/cloud_off:", color="orange")


# ---------- sidebar ----------

with st.sidebar:
    st.header("Inputs")
    upload = st.file_uploader("Sales history CSV", type="csv",
                              help="Columns: Date, Price_Charged, Quantity_Sold, optional Cost_Per_Unit, Competitor_Price")
    if upload is None:
        st.caption("No file uploaded: using the bundled sample data.")
        st.download_button("Download sample CSV", SAMPLE_PATH.read_bytes(), "sample_data.csv", "text/csv")

    country = st.selectbox("Target country", list(COUNTRY_MAP), format_func=lambda c: COUNTRY_MAP[c]["name"])
    sym = COUNTRY_MAP[country]["symbol"]

    timeframe = st.selectbox("Timeframe", list(PERIOD_MULT), help="All profit, revenue and cost figures are shown for this period.")
    default_cogs = st.number_input(f"Default COGS per unit ({sym})", min_value=0.0, value=DEFAULTS["cogs"],
                                   help="Used only for rows where the CSV has no Cost_Per_Unit.")
    fixed_monthly = st.number_input(f"Monthly fixed costs ({sym})", min_value=0.0, value=DEFAULTS["fixed_costs"], step=500.0,
                                    help="Rent, salaries, software… scaled to the selected timeframe.")
    capacity = st.number_input(f"Capacity / inventory ceiling ({PERIOD_LABEL[timeframe]}, units)", min_value=0,
                               value=0, step=500, help="Maximum units you can sell in the period. 0 = no limit.")
    import_share = st.slider("Share of COGS priced in USD (%)", 0, 100, int(DEFAULTS["import_share"]),
                             help="Only this share of unit cost moves with the exchange rate.")
    model_kind = st.radio("Demand model", ["linear", "loglog"], horizontal=True,
                          format_func=lambda k: "Linear" if k == "linear" else "Log-log (constant elasticity)")
    use_real = st.toggle("Adjust history for inflation", value=True,
                         help="Deflate historical prices with CPI before fitting demand, so price rises caused by inflation aren't mistaken for real price changes.")

# ---------- data ----------

st.title("Pricing Optimization Engine")
st.caption(f"Finds the profit-maximizing price from your sales history and stress-tests it against "
           f"{COUNTRY_MAP[country]['name']} inflation, exchange-rate and competitor shocks. Prices in {COUNTRY_MAP[country]['currency']}.")

raw = upload.getvalue() if upload is not None else SAMPLE_PATH.read_bytes()
try:
    agg, data_warnings = load_data(raw, default_cogs)
except (DataValidationError, ValueError) as e:
    st.error(f"Could not use this file: {e}")
    st.stop()

with st.spinner("Fetching inflation and exchange rates…"):
    infl, fx = cached_inflation(country), cached_fx(country)

agg, deflate_warnings = deflate(agg, infl.series if use_real else None)
if not use_real:
    deflate_warnings = []

models = {}
for kind in ("linear", "loglog"):
    try:
        models[kind] = fit_demand(agg, kind)
    except ValueError as e:
        models[kind] = e
model = models[model_kind]
if isinstance(model, Exception):
    st.error(f"Could not fit the {model_kind} demand model: {model}")
    st.stop()

current_price = float(agg["Price_Charged"].iloc[-1])
base_cogs = float(agg["Cost_Per_Unit"].iloc[-1])
base_comp = float(agg["Real_Competitor_Price"].iloc[-1]) if model.has_comp else None

with st.sidebar:
    max_price = st.number_input(f"Max price to test ({sym})", min_value=0.01,
                                value=float(round(2 * model.p_max, 2)), key=f"max_price_{model_kind}_{len(agg)}",
                                help="Upper bound of the price search. Default: 2× the highest historical price.")

# Live macro values become the slider defaults, refreshed whenever the country changes
if st.session_state.get("shock_country") != country:
    reset_shocks(infl, fx)
    st.session_state.shock_country = country

metrics_area = st.container()
charts_area = st.container()

# ---------- shock sliders (rendered below the charts) ----------

st.divider()
st.subheader("Macro shock simulation")
st.caption("Defaults come from live data: 12-month CPI inflation and the 12-month change in the local-currency/USD rate. "
           "Move them to test what-if scenarios.")
s1, s2, s3, s4 = st.columns([3, 3, 3, 1.4], vertical_alignment="bottom")
with s1:
    inflation = st.slider("Country inflation rate (%)", -10.0, 100.0, step=0.5, key="shock_infl",
                          help="Raises COGS and fixed costs.")
with s2:
    fx_shift = st.slider("Exchange rate shift (%)", -50.0, 100.0, step=0.5, key="shock_fx",
                         help="Change in local currency per USD. Positive = local currency weakens, so imported inputs cost more.",
                         disabled=country == "US")
with s3:
    comp_shift = st.slider("Competitor price change (%)", -50.0, 50.0, step=1.0, key="shock_comp",
                           disabled=not model.has_comp,
                           help=None if model.has_comp else "Needs a Competitor_Price column in the CSV.")
with s4:
    st.button("Reset to live data", on_click=reset_shocks, args=(infl, fx), width="stretch")
if not model.has_comp:
    st.caption("Competitor slider disabled: the uploaded data has no Competitor_Price column, so cross-price effects can't be estimated.")

# ---------- scenarios ----------

common = dict(base_cogs=base_cogs, fixed_monthly=fixed_monthly, capacity=capacity or np.inf, period=timeframe,
              import_share=import_share / 100, base_comp_price=base_comp, current_price=current_price, max_price=max_price)
result = run_scenario(model, ScenarioParams(**common, inflation=inflation / 100,
                                            fx_shift=(fx_shift if country != "US" else 0) / 100, comp_shift=comp_shift / 100))
today = run_scenario(model, ScenarioParams(**common))

opt, base = result.optimal, result.baseline
per = PERIOD_LABEL[timeframe]

# ---------- metrics ----------

with metrics_area:
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Optimal price", money(opt["price"], sym), f"{(opt['price'] / current_price - 1) * 100:+.1f}% vs current",
              help=f"Current price: {money(current_price, sym)}")
    c2.metric(f"Peak net profit ({per})", money(opt["profit"], sym), money(opt["profit"] - base["profit"], sym),
              help=f"Delta vs keeping the current price under the same scenario ({money(base['profit'], sym)}).")
    c3.metric("Price elasticity at optimum", f"{result.ped_opt:.2f}",
              help="% change in quantity for a 1% price change. Below -1 = elastic.")
    with c4:
        st.metric("Demand fit R²", f"{model.r2:.2f}", help="Share of month-to-month sales variation the model explains.")
        if model.kind == "loglog" and model.n_dropped:
            st.badge(f"{model.n_dropped} of {model.n + model.n_dropped} periods dropped (zero sales)",
                     icon=":material/warning:", color="orange")
    with c5:
        st.metric("CPI inflation (YoY)", f"{infl.value:.1f}%")
        macro_badge(infl, "CPI")
    with c6:
        st.metric(f"FX ({COUNTRY_MAP[country]['currency']} per USD)", f"{fx.value:,.4f}",
                  f"{fx.change_pct:+.1f}% 12m" if fx.change_pct is not None and country != "US" else None,
                  delta_color="inverse")
        macro_badge(fx, "FX")

    for w in model.warnings + result.warnings:
        st.warning(w, icon=":material/warning:")

# ---------- charts ----------

col = colors()
curve = result.curve

with charts_area:
    fig = go.Figure()
    cap = curve[curve["cap_binding"]]
    if not cap.empty:
        fig.add_vrect(x0=cap["price"].min(), x1=cap["price"].max(), fillcolor=col["band"], line_width=0,
                      annotation_text="capacity binding", annotation_position="top left")
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["profit"], name="Net profit", line=dict(color=col["s1"], width=2.5)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["revenue"], name="Revenue", line=dict(color=col["s2"], width=2)))
    fig.add_trace(go.Scatter(x=curve["price"], y=curve["total_cost"], name="Total cost", line=dict(color=col["s3"], width=2)))
    fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
    fig.add_vline(x=opt["price"], line=dict(color=col["s1"], width=1.5, dash="dot"),
                  annotation_text=f"Optimal {money(opt['price'], sym)}", annotation_position="top right")
    fig.add_vline(x=current_price, line=dict(color=col["muted"], width=1.5, dash="dash"),
                  annotation_text=f"Current {money(current_price, sym)}", annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[opt["price"]], y=[opt["profit"]], mode="markers", name="Peak profit",
                             marker=dict(color=col["s1"], size=11, line=dict(color="white", width=2)),
                             showlegend=False, hoverinfo="skip"))
    for be in result.break_evens:
        fig.add_trace(go.Scatter(x=[be], y=[0], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=col["muted"], size=9, symbol="diamond")))
    style(fig, f"Profit, revenue and cost vs price ({per})", f"Price ({sym})", f"{sym} {per}", height=460)
    fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}", selector=dict(mode="lines"))
    st.plotly_chart(fig, width="stretch")
    if result.break_evens:
        st.caption("Break-even price(s): " + ", ".join(money(b, sym) for b in result.break_evens)
                   + f" · Unit cost under scenario: {money(result.cogs_final, sym)} · Fixed costs: {money(result.fixed_final, sym)} {per}")

    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        price_col = "Real_Price"
        fig.add_trace(go.Scatter(x=agg[price_col], y=agg["Quantity_Sold"] * PERIOD_MULT[timeframe], mode="markers",
                                 name="Observed months", marker=dict(color=col["s2"], size=9, line=dict(color="white", width=1)),
                                 hovertemplate=f"{sym}%{{x:,.2f}} → %{{y:,.0f}} units<extra></extra>"))
        fig.add_trace(go.Scatter(x=curve["price"], y=curve["q_demand"], name="Fitted demand", line=dict(color=col["s1"], width=2),
                                 hovertemplate="%{y:,.0f} units<extra></extra>"))
        style(fig, f"Demand curve: units sold {per}", f"Price ({sym}, {'real' if use_real else 'nominal'})", "Units")
        fig.update_layout(hovermode="closest")
        st.plotly_chart(fig, width="stretch")
    with right:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=curve["price"], y=today.curve["profit"], name="Today's costs, no shock",
                                 line=dict(color=col["muted"], width=2, dash="dash")))
        fig.add_trace(go.Scatter(x=curve["price"], y=curve["profit"], name="Scenario", line=dict(color=col["s1"], width=2.5)))
        fig.add_hline(y=0, line=dict(color=col["muted"], width=1))
        style(fig, f"Shock impact on net profit ({per})", f"Price ({sym})", f"{sym} {per}")
        fig.update_traces(hovertemplate=f"{sym}%{{y:,.0f}}")
        st.plotly_chart(fig, width="stretch")
        d_price = opt["price"] - today.optimal["price"]
        d_profit = opt["profit"] - today.optimal["profit"]
        st.caption(f"Scenario moves the optimal price by {money(d_price, sym)} and peak profit by {money(d_profit, sym)} {per}.")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=agg.index, y=agg["Price_Charged"], name="Your price", line=dict(color=col["s1"], width=2)))
    if "Competitor_Price" in agg:
        fig.add_trace(go.Scatter(x=agg.index, y=agg["Competitor_Price"], name="Competitor price", line=dict(color=col["s2"], width=2)))
    if use_real and infl.series is not None:
        fig.add_trace(go.Scatter(x=agg.index, y=agg["Real_Price"], name="Your price (inflation-adjusted)",
                                 line=dict(color=col["s3"], width=2, dash="dot")))
    style(fig, "Price history (monthly average)", "", f"Price ({sym})", height=340)
    fig.update_traces(hovertemplate=f"{sym}%{{y:,.2f}}")
    st.plotly_chart(fig, width="stretch")

# ---------- details ----------

with st.expander("Model details and data notes"):
    m1, m2 = st.columns(2)
    with m1:
        st.markdown("**Fitted demand (monthly units)**")
        st.code(model.equation(), language=None)
        rows = []
        for kind, m in models.items():
            if isinstance(m, Exception):
                rows.append({"Model": kind, "R²": None, "Periods used": None, "Own-price coef": None})
            else:
                rows.append({"Model": kind, "R²": round(m.r2, 3), "Periods used": m.n, "Own-price coef": round(m.b, 3)})
        st.dataframe(pd.DataFrame(rows), hide_index=True)
        xed = result.xed_opt
        st.markdown(f"- Elasticity at current price: **{result.ped_current:.2f}**\n"
                    f"- Cross-price elasticity at optimum: **{xed:.2f}**" if xed is not None else
                    f"- Elasticity at current price: **{result.ped_current:.2f}**\n- Cross-price elasticity: n/a (no competitor data)")
        st.markdown(f"- Observed real price range: {money(model.p_min, sym)} – {money(model.p_max, sym)}")
    with m2:
        st.markdown("**Data notes**")
        notes = data_warnings + deflate_warnings + model.warnings
        if notes:
            for n in notes:
                st.markdown(f"- {n}")
        else:
            st.markdown("- No data issues found.")
        st.markdown(f"- {len(agg)} months of data, {agg.index.min():%b %Y} – {agg.index.max():%b %Y}")
    st.markdown("**Monthly aggregated data**")
    st.dataframe(agg.round(2), width="stretch")
