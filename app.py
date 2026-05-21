"""
AI Infrastructure Swing Trade Dashboard  —  app.py
Live price + technical indicator dashboard.
Watchlist and entry prices persisted in Supabase.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

import db  # Supabase persistence layer

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Infra Swing Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Supabase init (seed defaults if first run) ────────────────────────────────
try:
    db.seed_defaults_if_empty()
except Exception as e:
    st.warning(f"Supabase seed check failed: {e}")

# ── Load watchlist + entries from Supabase ────────────────────────────────────
@st.cache_data(ttl=30)
def get_watchlist() -> list[dict]:
    return db.load_watchlist()

@st.cache_data(ttl=15)
def get_entries() -> dict:
    return db.load_entries()

watchlist_rows = get_watchlist()
entries        = get_entries()

watchlist = {r["ticker"]: r for r in watchlist_rows}
tickers   = [r["ticker"] for r in watchlist_rows]   # rank-ordered

# ── Data fetching ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_quotes(tickers_tuple: tuple) -> dict:
    tickers = list(tickers_tuple)
    if not tickers:
        return {}
    raw = yf.download(
        tickers,
        period="1d",
        interval="1m",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )
    quotes = {}
    for ticker in tickers:
        try:
            df = raw if len(tickers) == 1 else raw[ticker]
            df = df.dropna()
            if df.empty:
                continue
            last  = df.iloc[-1]
            open_ = df.iloc[0]["Open"]
            quotes[ticker] = {
                "price":  round(float(last["Close"]), 2),
                "open":   round(float(open_), 2),
                "high":   round(float(df["High"].max()), 2),
                "low":    round(float(df["Low"].min()), 2),
                "volume": int(df["Volume"].sum()),
                "change": round(float(last["Close"]) - float(open_), 2),
                "pct":    round((float(last["Close"]) - float(open_)) / float(open_) * 100, 2),
            }
        except Exception:
            pass
    return quotes

@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval="1d",
                     auto_adjust=True, progress=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"]
    # RSI
    df["RSI_14"] = ta.momentum.RSIIndicator(close, window=14).rsi()
    # EMA
    df["EMA_50"]  = ta.trend.EMAIndicator(close, window=50).ema_indicator()
    df["EMA_200"] = ta.trend.EMAIndicator(close, window=200).ema_indicator()
    # MACD
    macd_ind = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df["MACD_12_26_9"]  = macd_ind.macd()
    df["MACDs_12_26_9"] = macd_ind.macd_signal()
    df["MACDh_12_26_9"] = macd_ind.macd_diff()
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df["BBU_20"] = bb.bollinger_hband()
    df["BBM_20"] = bb.bollinger_mavg()
    df["BBL_20"] = bb.bollinger_lband()
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")

    refresh_interval = st.selectbox(
        "Auto-refresh",
        [15, 30, 60, 120, 300],
        index=1,
        format_func=lambda x: f"{x}s" if x < 60 else f"{x//60}min",
    )
    show_chart        = st.checkbox("Show detail chart", value=True)
    chart_period      = st.selectbox("Chart lookback", ["1mo", "3mo", "6mo", "1y"], index=1)
    show_fundamentals = st.checkbox("Show fundamental scores", value=True)
    show_indicators   = st.checkbox("Show RSI / MACD table", value=True)

    st.markdown("---")
    st.markdown("### 📌 Entry prices")
    st.caption("Saved to Supabase — persists across sessions")

    updated_entries = {}
    for ticker in tickers:
        val = entries.get(ticker)
        new_val = st.number_input(
            ticker,
            min_value=0.0,
            value=float(val) if val else 0.0,
            step=0.01,
            format="%.2f",
            key=f"entry_{ticker}",
        )
        updated_entries[ticker] = new_val if new_val > 0 else None

    if st.button("💾 Save entry prices", use_container_width=True):
        db.set_entries_bulk(updated_entries)
        st.cache_data.clear()
        st.success("Entry prices saved to Supabase ✓")

    st.markdown("---")
    st.page_link("pages/1_Admin.py", label="🛠️ Manage watchlist")
    st.markdown("---")
    st.caption(
        f"Yahoo Finance · ~15-min delay\n"
        f"Refreshes every {refresh_interval}s · "
        f"{len(tickers)} tickers tracked"
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📡 AI Infrastructure — Swing Trade Dashboard")
c1, c2 = st.columns([3, 1])
c1.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Data delayed ~15 min")
c2.caption("Ranked: OCF → Low Debt")
st.divider()

# ── Fetch quotes ──────────────────────────────────────────────────────────────
with st.spinner("Fetching live quotes…"):
    quotes = fetch_quotes(tuple(tickers))

# ── Summary metrics ───────────────────────────────────────────────────────────
gainers = sum(1 for t in tickers if quotes.get(t, {}).get("pct", 0) > 0)
losers  = len(tickers) - gainers
avg_pct = (sum(quotes.get(t, {}).get("pct", 0) for t in tickers) / len(tickers)) if tickers else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Tickers tracked", len(tickers))
m2.metric("Gainers", gainers)
m3.metric("Losers", losers, delta_color="inverse")
m4.metric("Avg day change", f"{avg_pct:+.2f}%")
m5.metric("Quotes live", len(quotes))

st.divider()

# ── Watchlist table ───────────────────────────────────────────────────────────
st.markdown("### Watchlist")

rows = []
for ticker in tickers:
    meta  = watchlist[ticker]
    q     = quotes.get(ticker, {})
    price = q.get("price")
    entry = entries.get(ticker)
    pl_pct = round((price - entry) / entry * 100, 2) if (entry and price) else None

    rows.append({
        "Rank":       meta["rank"],
        "Ticker":     ticker,
        "Company":    meta["name"],
        "Sector":     meta["sector"],
        "Price":      f"${price:,.2f}" if price else "—",
        "Day %":      f"{q.get('pct', 0):+.2f}%" if price else "—",
        "P/L %":      f"{pl_pct:+.2f}%" if pl_pct is not None else "—",
        "Volume":     f"{q.get('volume', 0)/1e6:.1f}M" if price else "—",
        "OCF Score":  meta["ocf_score"],
        "Debt Score": meta["debt_score"],
        "OCF":        meta["ocf_label"],
        "LT Debt":    meta["debt_label"],
        "D/E":        float(meta["de_ratio"]),
    })

df_table = pd.DataFrame(rows)

display_cols = ["Rank", "Ticker", "Company", "Sector", "Price", "Day %"]
if any(entries.values()):
    display_cols.append("P/L %")
display_cols.append("Volume")
if show_fundamentals:
    display_cols += ["OCF Score", "Debt Score", "OCF", "LT Debt", "D/E"]

st.dataframe(
    df_table[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank":       st.column_config.NumberColumn(width="small"),
        "Ticker":     st.column_config.TextColumn(width="small"),
        "Price":      st.column_config.TextColumn(width="small"),
        "Day %":      st.column_config.TextColumn(width="small"),
        "P/L %":      st.column_config.TextColumn(width="small"),
        "Volume":     st.column_config.TextColumn(width="small"),
        "OCF Score":  st.column_config.ProgressColumn("OCF Score",  min_value=0, max_value=100, width="medium"),
        "Debt Score": st.column_config.ProgressColumn("Debt Score", min_value=0, max_value=100, width="medium"),
        "D/E":        st.column_config.NumberColumn(format="%.2f", width="small"),
    },
)

st.divider()

# ── Technical indicators ──────────────────────────────────────────────────────
if show_indicators:
    st.markdown("### Technical indicators (daily)")
    with st.spinner("Computing RSI / MACD…"):
        ind_rows = []
        for ticker in tickers:
            try:
                hist  = fetch_history(ticker, period=chart_period)
                hist  = compute_indicators(hist)
                price = quotes.get(ticker, {}).get("price")

                rsi    = hist["RSI_14"].iloc[-1]        if "RSI_14" in hist.columns        else None
                macd   = hist["MACD_12_26_9"].iloc[-1]  if "MACD_12_26_9" in hist.columns  else None
                macds  = hist["MACDs_12_26_9"].iloc[-1] if "MACDs_12_26_9" in hist.columns else None
                ema50  = hist["EMA_50"].iloc[-1]         if "EMA_50" in hist.columns         else None
                ema200 = hist["EMA_200"].iloc[-1]        if "EMA_200" in hist.columns        else None

                ind_rows.append({
                    "Ticker":      ticker,
                    "RSI (14)":    round(float(rsi), 1) if rsi is not None and not pd.isna(rsi) else None,
                    "RSI signal":  ("OB ⚠️" if rsi >= 75 else ("OS 🟢" if rsi <= 35 else "Neutral")) if (rsi is not None and not pd.isna(rsi)) else "—",
                    "MACD signal": ("Bull 🟢" if macd > macds else "Bear 🔴") if (macd is not None and macds is not None and not pd.isna(macd) and not pd.isna(macds)) else "—",
                    "MACD value":  round(float(macd), 3) if macd is not None and not pd.isna(macd) else None,
                    "MA cross":    ("Golden ✅" if ema50 > ema200 else "Death ❌") if (ema50 is not None and ema200 is not None and not pd.isna(ema50) and not pd.isna(ema200)) else "—",
                    "vs EMA-50":   (f"+{((price-ema50)/ema50*100):.1f}%" if price > ema50 else f"{((price-ema50)/ema50*100):.1f}%") if (price and ema50 is not None and not pd.isna(ema50)) else "—",
                    "EMA-50":      f"${float(ema50):.2f}"  if ema50  is not None and not pd.isna(ema50)  else "—",
                    "EMA-200":     f"${float(ema200):.2f}" if ema200 is not None and not pd.isna(ema200) else "—",
                })
            except Exception:
                ind_rows.append({
                    "Ticker": ticker, "RSI (14)": None, "RSI signal": "Error",
                    "MACD signal": "—", "MACD value": None,
                    "MA cross": "—", "vs EMA-50": "—", "EMA-50": "—", "EMA-200": "—",
                })

    st.dataframe(
        pd.DataFrame(ind_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "RSI (14)":   st.column_config.NumberColumn(format="%.1f", width="small"),
            "MACD value": st.column_config.NumberColumn(format="%.3f", width="small"),
        },
    )
    st.divider()

# ── Detail chart ──────────────────────────────────────────────────────────────
if show_chart and tickers:
    st.markdown("### Detail chart")
    selected = st.selectbox(
        "Select ticker",
        tickers,
        format_func=lambda t: f"{t} — {watchlist[t]['name']}",
    )
    with st.spinner(f"Loading chart for {selected}…"):
        hist = fetch_history(selected, period=chart_period)
        hist = compute_indicators(hist)

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.04, row_heights=[0.55, 0.22, 0.23],
        subplot_titles=[f"{selected} · Price & Bands", "RSI (14)", "MACD (12/26/9)"],
    )

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"], name="Price",
        increasing_line_color="#1D9E75", decreasing_line_color="#E24B4A",
    ), row=1, col=1)

    if "BBU_20" in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["BBU_20"], name="BB Upper",
                                 line=dict(color="#B5D4F4", width=1, dash="dot")), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist["BBM_20"], name="BB Mid",
                                 line=dict(color="#888780", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist["BBL_20"], name="BB Lower",
                                 line=dict(color="#B5D4F4", width=1, dash="dot"),
                                 fill="tonexty", fillcolor="rgba(181,212,244,0.08)"), row=1, col=1)
    if "EMA_50" in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["EMA_50"], name="EMA 50",
                                 line=dict(color="#EF9F27", width=1.5)), row=1, col=1)
    if "EMA_200" in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["EMA_200"], name="EMA 200",
                                 line=dict(color="#D4537E", width=1.5, dash="dash")), row=1, col=1)

    entry_price = entries.get(selected)
    if entry_price:
        fig.add_hline(y=entry_price, line_dash="dash", line_color="#7F77DD",
                      annotation_text=f"Entry ${entry_price:.2f}",
                      annotation_position="bottom right", row=1, col=1)

    if "RSI_14" in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["RSI_14"], name="RSI",
                                 line=dict(color="#378ADD", width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#BA7517", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#1D9E75", row=2, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(186,117,23,0.07)", row=2, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(29,158,117,0.07)", row=2, col=1)

    if "MACD_12_26_9" in hist.columns and "MACDs_12_26_9" in hist.columns:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MACD_12_26_9"], name="MACD",
                                 line=dict(color="#378ADD", width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MACDs_12_26_9"], name="Signal",
                                 line=dict(color="#D4537E", width=1.5)), row=3, col=1)
    if "MACDh_12_26_9" in hist.columns:
        colors = ["#1D9E75" if v >= 0 else "#E24B4A" for v in hist["MACDh_12_26_9"].fillna(0)]
        fig.add_trace(go.Bar(x=hist.index, y=hist["MACDh_12_26_9"], name="Histogram",
                             marker_color=colors, opacity=0.6), row=3, col=1)

    fig.update_layout(
        height=680, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    fund = watchlist[selected]
    fc1, fc2, fc3, fc4 = st.columns(4)
    fc1.metric("Rank",    f"#{fund['rank']}")
    fc2.metric("OCF",     fund["ocf_label"])
    fc3.metric("LT Debt", fund["debt_label"])
    fc4.metric("D/E",     f"{float(fund['de_ratio']):.2f}")
    if fund.get("notes"):
        st.caption(f"💬 {fund['notes']}")

st.divider()

# ── Correlation heatmap ───────────────────────────────────────────────────────
with st.expander("📊 30-day return correlation heatmap", expanded=False):
    st.caption("Helps identify diversification within the watchlist")
    with st.spinner("Computing correlations…"):
        try:
            price_data = {}
            for t in tickers:
                h = fetch_history(t, period="1mo")
                if not h.empty:
                    price_data[t] = h["Close"]
            corr = pd.DataFrame(price_data).dropna().pct_change().corr().round(2)
            fig_corr = go.Figure(go.Heatmap(
                z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
                colorscale=[[0, "#E24B4A"], [0.5, "#F1EFE8"], [1, "#1D9E75"]],
                zmin=-1, zmax=1,
                text=corr.values.round(2), texttemplate="%{text}",
                textfont=dict(size=11),
            ))
            fig_corr.update_layout(
                height=420, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        except Exception as e:
            st.error(f"Correlation error: {e}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<p style='font-size:11px;color:gray;margin-top:1.5rem;'>"
    "⚠️ Educational purposes only — not investment advice. "
    "Data from Yahoo Finance (~15-min delayed). "
    "Verify with your broker before executing any trade."
    "</p>",
    unsafe_allow_html=True,
)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
time.sleep(refresh_interval)
st.rerun()
