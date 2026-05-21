# AI Infrastructure Swing Trade Dashboard

A live technical analysis dashboard for the top 10 AI infrastructure stocks, ranked by operating cash flow and debt safety.

## Features

- **Live quotes** — price, day change %, volume (Yahoo Finance, ~15-min delay)
- **Entry price tracking** — set your entry per ticker, track P/L % in real time
- **Technical indicators** — RSI (14), MACD (12/26/9), EMA 50/200, Bollinger Bands
- **Candlestick chart** — with all overlays for any selected ticker
- **Correlation heatmap** — 30-day return correlation across the watchlist
- **Fundamental scores** — OCF and debt safety scores from the original analysis
- **Auto-refresh** — configurable from 15s to 5 minutes

## Watchlist

| Rank | Ticker | Company | Sector |
|------|--------|---------|--------|
| 1 | NVDA | NVIDIA Corporation | Semiconductors |
| 2 | AVGO | Broadcom Inc. | Semiconductors |
| 3 | TSM | Taiwan Semiconductor | Semiconductors |
| 4 | ANET | Arista Networks | Networking |
| 5 | APH | Amphenol Corp. | Components |
| 6 | MU | Micron Technology | Memory |
| 7 | SNDK | SanDisk Corp. | Storage |
| 8 | VRT | Vertiv Holdings | Infrastructure |
| 9 | WDC | Western Digital | Storage |
| 10 | EME | EMCOR Group | Construction |

---

## Local setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ai-infra-dashboard.git
cd ai-infra-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Deploy to Streamlit Cloud (free)

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app**
4. Select your repo, branch (`main`), and set **Main file path** to `app.py`
5. Click **Deploy** — done in ~2 minutes

> **Note:** `entries.json` (your entry prices) is gitignored and won't persist across Streamlit Cloud restarts. For persistent storage on Cloud, switch the JSON file to `st.session_state` or use a free Supabase/Notion database backend.

---

## Project structure

```
ai-infra-dashboard/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Theme and server config
├── .gitignore
└── README.md
```

---

## Customising the watchlist

Edit the `DEFAULT_WATCHLIST` dict at the top of `app.py`:

```python
DEFAULT_WATCHLIST = {
    "NVDA": {"name": "NVIDIA Corporation", "rank": 1, "sector": "Semiconductors", "entry": None},
    # Add or remove tickers here
}
```

Also update `FUNDAMENTALS` dict with your own OCF/debt scores if you change tickers.

---

## Data notes

- Yahoo Finance provides ~15-minute delayed quotes during market hours
- Historical OHLCV is fetched for the selected chart lookback period (1mo / 3mo / 6mo / 1y)
- `@st.cache_data(ttl=60)` caches live quotes for 60s; historical data cached for 5 minutes
- Indicators computed via `pandas-ta` on the client — no external API calls needed

---

## Disclaimer

> This dashboard is for **educational and informational purposes only**. It does not constitute investment advice. Swing trading involves significant risk of capital loss. Always verify data with your broker before executing any trade.
