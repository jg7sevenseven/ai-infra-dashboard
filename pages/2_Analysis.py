"""
pages/2_Analysis.py
Original AI infrastructure swing trade analysis — rationale, signals,
and fundamental scores that produced the top-10 ranked watchlist.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

st.set_page_config(
    page_title="Swing Trade Analysis",
    page_icon="🔬",
    layout="wide",
)

st.markdown("# 🔬 AI Infrastructure — Swing Trade Analysis")
st.caption("Original technical & fundamental analysis underpinning the watchlist rankings · May 2026")
st.page_link("app.py", label="← Back to live dashboard")
st.divider()

# ── Scoring data ──────────────────────────────────────────────────────────────
ANALYSIS = [
    {
        "rank": 1, "ticker": "NVDA", "name": "NVIDIA Corporation",
        "sector": "Semiconductors", "ocf_score": 100, "debt_score": 96,
        "ocf_label": "$64.1B", "debt_label": "~$8.5B", "de_ratio": 0.10,
        "price_ref": "$226–228", "rsi": 71, "macd_signal": "Bull",
        "macd_value": "+4.46", "ma_cross": "Golden ✅",
        "setup": "Momentum continuation",
        "signal_color": "#1D9E75",
        "thesis": (
            "MACD crossed positive May 8 with price in a clean bullish MA stack "
            "(5d > 50d > 200d). Post-earnings momentum from Q1 FY2026 driven by "
            "Blackwell GPU ramp. RSI at 71 is elevated but not yet disqualifying "
            "for a weekly swing — still room before hard overbought territory. "
            "Dominant OCF in the cohort at $64.1B with minimal net leverage "
            "(D/E ~0.10). Preferred entry on any 1–2% intraday dip."
        ),
        "risks": "RSI approaching overbought; any macro risk-off move hits semis first.",
        "target": "+5–8% weekly swing target; stop below 50d EMA",
    },
    {
        "rank": 2, "ticker": "AVGO", "name": "Broadcom Inc.",
        "sector": "Semiconductors", "ocf_score": 87, "debt_score": 72,
        "ocf_label": "$26.9B FCF", "debt_label": "$63.8B", "de_ratio": 0.80,
        "price_ref": "$418–422", "rsi": 84, "macd_signal": "Bull",
        "macd_value": "+6.17", "ma_cross": "Golden ✅",
        "setup": "Overbought — wait for pullback",
        "signal_color": "#EF9F27",
        "thesis": (
            "All 12 MAs aligned as buy signals with MACD at +6.17. Anthropic "
            "multi-gigawatt deal and hyperscaler custom ASIC pipeline (XPUs) "
            "provide strong fundamental tailwind. D/E of 0.80 is manageable "
            "given $14.2B cash and $26.9B FCF. RSI at 84 is the key caution — "
            "wait for a 2–4% consolidation before initiating a weekly long. "
            "Strong buy on the dip; not a chase at current levels."
        ),
        "risks": "RSI 84 — hardest overbought in cohort; debt load elevated post-VMware.",
        "target": "Enter on 2–4% pullback; target prior ATH retest",
    },
    {
        "rank": 3, "ticker": "TSM", "name": "Taiwan Semiconductor Mfg.",
        "sector": "Semiconductors", "ocf_score": 83, "debt_score": 92,
        "ocf_label": "NT$2,275B", "debt_label": "NT$896B", "de_ratio": 0.18,
        "price_ref": "$183–190", "rsi": 71, "macd_signal": "Bull",
        "macd_value": "Above signal", "ma_cross": "Golden ✅",
        "setup": "Momentum continuation",
        "signal_color": "#1D9E75",
        "thesis": (
            "Full-year 2025 revenue +31.6% YoY; EPS +46.4% — best fundamental "
            "growth in cohort. OCF covers debt 229% — exceptional balance sheet "
            "safety with D/E of only 0.18. MACD above signal confirms bullish "
            "weekly trend. RSI at 71 mirrors NVDA — momentum intact but extended. "
            "N2 process node ramp in H2 2026 is the catalyst. GeoPolitical "
            "headline risk (Taiwan Strait) is the primary binary risk for swing traders."
        ),
        "risks": "Taiwan geopolitical risk is the dominant tail risk — use tighter stops.",
        "target": "+4–6% weekly; stop below recent support ~$178",
    },
    {
        "rank": 4, "ticker": "ANET", "name": "Arista Networks",
        "sector": "Networking", "ocf_score": 67, "debt_score": 100,
        "ocf_label": "$4.3B FCF", "debt_label": "$0", "de_ratio": 0.00,
        "price_ref": "$140–155", "rsi": 38, "macd_signal": "Recovering",
        "macd_value": "Negative / improving", "ma_cross": "Recovering",
        "setup": "Oversold reversal / contrarian long",
        "signal_color": "#378ADD",
        "thesis": (
            "Zero debt — best balance sheet in the cohort outright. RSI at 38 "
            "with Williams %R at -92 signals deep oversold conditions. A 20% "
            "post-Q1 earnings sell-the-news correction from ATH $179.80 created "
            "the setup. Q1 2026 revenue beat: $2.71B vs $2.62B expected — "
            "fundamentals remain intact. AI network demand (400G/800G switching) "
            "is structurally growing. Contrarian weekly long targeting reversion "
            "toward $165–170. Best risk/reward entry in the cohort."
        ),
        "risks": "Post-earnings sentiment overhang may take time to clear; patience required.",
        "target": "Reversion to $165–170 (~10–15% from lows); stop below $138",
    },
    {
        "rank": 5, "ticker": "APH", "name": "Amphenol Corp.",
        "sector": "Components", "ocf_score": 66, "debt_score": 55,
        "ocf_label": "$4.4B FCF", "debt_label": "$14.6B", "de_ratio": 0.75,
        "price_ref": "$125–127", "rsi": 57, "macd_signal": "Bull",
        "macd_value": "Positive", "ma_cross": "Golden ✅",
        "setup": "Clean mid-range entry",
        "signal_color": "#1D9E75",
        "thesis": (
            "Record quarterly results in 2025 driven by exceptional IT datacom "
            "(AI data center) organic growth. FCF doubled YoY (+103.7%) — "
            "strongest FCF acceleration in cohort. Diversified connector exposure "
            "across data center, defense, and autos provides resilience vs "
            "pure-play semiconductor names. RSI in neutral zone (~57) is the "
            "cleanest entry signal in the top-5. Debt ($14.6B) partially offset "
            "by $11.1B cash position."
        ),
        "risks": "Elevated debt; exposure to defense/auto cycles beyond AI data center.",
        "target": "+4–6% weekly swing; neutral RSI gives most room to run in the short term",
    },
    {
        "rank": 6, "ticker": "MU", "name": "Micron Technology",
        "sector": "Memory", "ocf_score": 63, "debt_score": 50,
        "ocf_label": "Strong positive", "debt_label": "$15.0B", "de_ratio": 0.45,
        "price_ref": "$730–760", "rsi": 67, "macd_signal": "Bull",
        "macd_value": "+18.62", "ma_cross": "Golden ✅",
        "setup": "Breakout momentum",
        "signal_color": "#1D9E75",
        "thesis": (
            "MACD at +18.62 — strongest absolute momentum signal in the cohort. "
            "Price above all key MAs in a clean bullish stack. EPS jumped 8x YoY "
            "in Q2 FY2026; Q3 guidance implies 10x YoY jump. 'Memory crunch' "
            "narrative driving strong analyst upgrades across the street. "
            "HBM3E supply tightness through 2026 is the structural tailwind. "
            "$15B debt is the key concern but offset by surging earnings trajectory. "
            "Breakout candidate above $760 resistance."
        ),
        "risks": "Memory is cyclical — sentiment can reverse fast; debt load limits safety margin.",
        "target": "Breakout above $760 targets $800+; stop below $710",
    },
    {
        "rank": 7, "ticker": "SNDK", "name": "SanDisk Corp.",
        "sector": "Storage", "ocf_score": 58, "debt_score": 80,
        "ocf_label": "$1.5B H1 FY26", "debt_label": "$583M", "de_ratio": 0.15,
        "price_ref": "~$900–950", "rsi": 80, "macd_signal": "Bull",
        "macd_value": "Strong positive", "ma_cross": "Golden ✅",
        "setup": "Overbought — wait for consolidation",
        "signal_color": "#EF9F27",
        "thesis": (
            "Revenue +251% YoY in H1 FY2026 — most explosive top-line growth in "
            "cohort. Debt slashed from $1.8B to $583M in one half-year using OCF. "
            "Golden cross (50d > 200d) confirms bullish structural trend. "
            "ChartMill rates technical setup 10/10. However RSI at 80 is hard "
            "overbought — this is a wait-for-consolidation setup, not a chase. "
            "Target a 5–8% pullback to enter a weekly swing with better R/R."
        ),
        "risks": "RSI 80 — second most overbought after AVGO; new spin-off from WDC adds uncertainty.",
        "target": "Enter on 5–8% pullback; then target prior highs",
    },
    {
        "rank": 8, "ticker": "VRT", "name": "Vertiv Holdings",
        "sector": "Infrastructure", "ocf_score": 55, "debt_score": 62,
        "ocf_label": "$2.1B", "debt_label": "$2.9B", "de_ratio": 0.74,
        "price_ref": "~$120–130", "rsi": 60, "macd_signal": "Bull",
        "macd_value": "Positive", "ma_cross": "Golden ✅",
        "setup": "Steady uptrend",
        "signal_color": "#1D9E75",
        "thesis": (
            "Direct thermal/power infrastructure play on AI data center density "
            "scaling — as GPU racks go from 10kW to 100kW+, VRT's liquid cooling "
            "and power distribution become mission-critical. Co-developing 800V DC "
            "architecture with NVIDIA for Rubin Ultra. Interest coverage at 21.3x "
            "is extremely comfortable despite $2.9B debt. OCF grew from $900M to "
            "$2.1B over three years. EPS +166% FY2025. Projected 34%/47% "
            "revenue/earnings growth in FY2026."
        ),
        "risks": "Elevated debt; valuation pricing in significant growth already.",
        "target": "+5–7% weekly swing; steady uptrend with manageable pullback risk",
    },
    {
        "rank": 9, "ticker": "WDC", "name": "Western Digital",
        "sector": "Storage", "ocf_score": 48, "debt_score": 44,
        "ocf_label": "Positive / growing", "debt_label": "Moderate", "de_ratio": 0.60,
        "price_ref": "~$60–70", "rsi": 62, "macd_signal": "Bull",
        "macd_value": "Positive", "ma_cross": "Golden ✅",
        "setup": "Momentum — use tighter stops",
        "signal_color": "#EF9F27",
        "thesis": (
            "HDD market consolidating to 3 players (WDC, Seagate, Toshiba) — "
            "structural pricing power through at least 2030 per Morningstar. "
            "AI data center storage demand driving ePMR 32TB+ capacity cycles. "
            "Morningstar revised fair value +50% following Q4 2025 results. "
            "2026 YTD gain ~180% reflects market re-rating of the HDD oligopoly. "
            "Ranked lower due to higher relative debt and less dominant OCF vs "
            "semiconductor peers. Use tighter stops given elevated valuation."
        ),
        "risks": "Highest debt/OCF ratio in cohort; HDD secular decline risk long-term.",
        "target": "+3–5% weekly swing; tight stops given valuation stretch",
    },
    {
        "rank": 10, "ticker": "EME", "name": "EMCOR Group",
        "sector": "Construction", "ocf_score": 42, "debt_score": 76,
        "ocf_label": "Steady positive", "debt_label": "Low", "de_ratio": 0.20,
        "price_ref": "~$380–400", "rsi": 52, "macd_signal": "Neutral/Bull",
        "macd_value": "Slightly positive", "ma_cross": "Golden ✅",
        "setup": "Defensive AI exposure",
        "signal_color": "#5DCAA5",
        "thesis": (
            "Electrical infrastructure and mechanical/cooling systems contractor "
            "for AI data centers — the 'picks and shovels' play on hyperscaler "
            "capex. Low debt profile (D/E 0.20) and steady OCF make it the most "
            "defensive name in the list. Lower beta vs semiconductor names — "
            "suitable for traders wanting AI infrastructure exposure with reduced "
            "volatility. Expanding backlog from hyperscaler DC construction "
            "programs provides 2–3 year revenue visibility. Zacks #2 Buy."
        ),
        "risks": "Slowest growth profile; construction cycles can delay revenue recognition.",
        "target": "+3–4% weekly swing; best used as portfolio ballast vs high-beta semis",
    },
]

# ── Methodology banner ────────────────────────────────────────────────────────
with st.expander("📐 Ranking methodology", expanded=False):
    st.markdown("""
**Universe:** AI infrastructure stocks spanning semiconductors, networking, components,
memory, storage, power/thermal infrastructure, and data center construction.

**Primary sort key — Operating Cash Flow (OCF):**
Positive and growing OCF indicates a business generating real cash from AI infrastructure
demand — not just accounting profits. Scored 0–100 relative to cohort peers.

**Secondary sort key — Debt safety:**
Low leverage preserves optionality in a volatile rate environment and reduces
tail risk on any market dislocation. Scored 0–100 on D/E ratio, interest coverage,
and absolute debt level relative to cash.

**Technical overlay (used for entry timing, not ranking):**
- RSI (14): overbought >75, oversold <35
- MACD (12/26/9): signal line cross direction
- EMA 50/200: golden/death cross for trend confirmation
- Bollinger Bands (20, 2σ): for volatility context

**Swing trade frame:** Weekly (3–7 trading days). Positions are sized for
defined risk — always use stops.
    """)

st.divider()

# ── Summary scoring chart ─────────────────────────────────────────────────────
st.markdown("### Composite score — OCF vs Debt safety")

df_scores = pd.DataFrame([{
    "Ticker":     a["ticker"],
    "OCF Score":  a["ocf_score"],
    "Debt Score": a["debt_score"],
    "Composite":  round((a["ocf_score"] * 0.6 + a["debt_score"] * 0.4), 1),
    "Sector":     a["sector"],
    "RSI":        a["rsi"],
} for a in ANALYSIS])

col_chart, col_scatter = st.columns(2)

with col_chart:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="OCF Score (60%)",
        x=df_scores["Ticker"],
        y=df_scores["OCF Score"] * 0.6,
        marker_color="#1D9E75",
    ))
    fig_bar.add_trace(go.Bar(
        name="Debt Score (40%)",
        x=df_scores["Ticker"],
        y=df_scores["Debt Score"] * 0.4,
        marker_color="#378ADD",
    ))
    fig_bar.update_layout(
        barmode="stack", height=320,
        title="Composite ranking score by ticker",
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.2),
    )
    fig_bar.update_xaxes(showgrid=False)
    fig_bar.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", range=[0, 100])
    st.plotly_chart(fig_bar, use_container_width=True)

with col_scatter:
    fig_scat = go.Figure()
    for _, row in df_scores.iterrows():
        fig_scat.add_trace(go.Scatter(
            x=[row["Debt Score"]],
            y=[row["OCF Score"]],
            mode="markers+text",
            text=[row["Ticker"]],
            textposition="top center",
            marker=dict(size=row["RSI"] / 5 + 8, color=row["Composite"],
                        colorscale="Teal", showscale=False,
                        line=dict(color="white", width=1)),
            name=row["Ticker"],
            showlegend=False,
        ))
    fig_scat.add_vline(x=70, line_dash="dot", line_color="rgba(128,128,128,0.4)")
    fig_scat.add_hline(y=70, line_dash="dot", line_color="rgba(128,128,128,0.4)")
    fig_scat.update_layout(
        height=320,
        title="OCF vs Debt safety (bubble = RSI size)",
        xaxis_title="Debt Score →  safer",
        yaxis_title="OCF Score →  stronger",
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig_scat.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", range=[30, 110])
    fig_scat.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", range=[30, 110])
    st.plotly_chart(fig_scat, use_container_width=True)

st.divider()

# ── RSI snapshot bar ──────────────────────────────────────────────────────────
st.markdown("### RSI snapshot at time of analysis")
fig_rsi = go.Figure()
rsi_colors = ["#E24B4A" if r >= 75 else ("#1D9E75" if r <= 35 else "#378ADD")
              for r in df_scores["RSI"]]
fig_rsi.add_trace(go.Bar(
    x=df_scores["Ticker"], y=df_scores["RSI"],
    marker_color=rsi_colors,
    text=df_scores["RSI"], textposition="outside",
))
fig_rsi.add_hline(y=75, line_dash="dot", line_color="#E24B4A",
                  annotation_text="Overbought 75", annotation_position="right")
fig_rsi.add_hline(y=35, line_dash="dot", line_color="#1D9E75",
                  annotation_text="Oversold 35", annotation_position="right")
fig_rsi.add_hrect(y0=75, y1=100, fillcolor="rgba(226,75,74,0.07)")
fig_rsi.add_hrect(y0=0,  y1=35,  fillcolor="rgba(29,158,117,0.07)")
fig_rsi.update_layout(
    height=280, margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(range=[0, 105]),
)
fig_rsi.update_xaxes(showgrid=False)
fig_rsi.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
st.plotly_chart(fig_rsi, use_container_width=True)
st.caption("🔴 Overbought (>75) — wait for pullback  ·  🔵 Neutral  ·  🟢 Oversold (<35) — reversal setup")

st.divider()

# ── Individual stock cards ────────────────────────────────────────────────────
st.markdown("### Stock-by-stock analysis")

# Load live watchlist notes if available
try:
    wl = {r["ticker"]: r for r in db.load_watchlist()}
except Exception:
    wl = {}

for a in ANALYSIS:
    is_top3 = a["rank"] <= 3
    border  = "border-left: 3px solid #1D9E75;" if is_top3 else ""

    with st.container():
        st.markdown(
            f"<div style='padding:0.1rem 0 0.1rem 0.75rem; {border}'>",
            unsafe_allow_html=True,
        )

        h1, h2, h3 = st.columns([0.5, 4, 2])
        rank_bg = "#1D9E75" if is_top3 else "#2A2D35"
        h1.markdown(
            f"<div style='background:{rank_bg};color:white;border-radius:50%;"
            f"width:32px;height:32px;display:flex;align-items:center;"
            f"justify-content:center;font-weight:500;font-size:14px;margin-top:4px'>"
            f"#{a['rank']}</div>",
            unsafe_allow_html=True,
        )
        h2.markdown(f"**{a['ticker']}** &nbsp; {a['name']} &nbsp; "
                    f"<span style='font-size:12px;color:gray'>{a['sector']}</span>",
                    unsafe_allow_html=True)
        with h3:
            badges = []
            if a["macd_signal"] == "Bull":
                badges.append("🟢 MACD Bull")
            elif a["macd_signal"] == "Recovering":
                badges.append("🔵 MACD Recovering")
            rsi = a["rsi"]
            if rsi >= 75:
                badges.append(f"🔴 RSI {rsi} OB")
            elif rsi <= 35:
                badges.append(f"🟢 RSI {rsi} OS")
            else:
                badges.append(f"🔵 RSI {rsi}")
            if a["ma_cross"] == "Golden ✅":
                badges.append("✅ Golden cross")
            st.caption("  ·  ".join(badges))

        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Price (ref)", a["price_ref"])
        c2.metric("OCF score",   f"{a['ocf_score']}/100")
        c3.metric("Debt score",  f"{a['debt_score']}/100")
        c4.metric("D/E ratio",   f"{a['de_ratio']:.2f}")
        c5.metric("OCF (ann.)",  a["ocf_label"])
        c6.metric("LT Debt",     a["debt_label"])

        ta1, ta2 = st.columns([2, 1])
        with ta1:
            st.markdown("**Thesis**")
            st.markdown(f"<p style='font-size:13px;line-height:1.7;color:var(--text-color)'>{a['thesis']}</p>",
                        unsafe_allow_html=True)
        with ta2:
            st.markdown("**Setup**")
            st.markdown(
                f"<span style='background:{a['signal_color']}22;color:{a['signal_color']};"
                f"padding:2px 10px;border-radius:99px;font-size:12px;font-weight:500'>"
                f"{a['setup']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(" ")
            st.markdown(f"🎯 **Target:** {a['target']}")
            st.markdown(f"⚠️ **Risk:** {a['risks']}")

        st.markdown("</div>", unsafe_allow_html=True)
        st.divider()

# ── Sector allocation pie ─────────────────────────────────────────────────────
st.markdown("### Sector allocation across watchlist")
sector_counts = pd.Series([a["sector"] for a in ANALYSIS]).value_counts()
fig_pie = go.Figure(go.Pie(
    labels=sector_counts.index,
    values=sector_counts.values,
    hole=0.4,
    marker_colors=["#1D9E75","#378ADD","#EF9F27","#D4537E","#7F77DD","#5DCAA5"],
))
fig_pie.update_layout(
    height=300, margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="rgba(0,0,0,0)",
    legend=dict(orientation="h", y=-0.1),
)
st.plotly_chart(fig_pie, use_container_width=True)

st.divider()
st.markdown(
    "<p style='font-size:11px;color:gray;'>"
    "⚠️ Analysis reflects conditions as of May 2026. "
    "Technical signals change daily — always verify current indicators on the live dashboard. "
    "Not investment advice. Verify with your broker before executing any trade."
    "</p>",
    unsafe_allow_html=True,
)
