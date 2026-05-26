"""
db.py — Supabase persistence layer (direct httpx, no supabase-py client)
Works with both legacy anon keys and new sb_publishable_ keys.

Tables required (run supabase_setup.sql to create):
  watchlist   — ticker metadata + fundamental scores
  entries     — per-ticker entry prices
"""

from __future__ import annotations
from typing import Optional
import streamlit as st
import httpx


# ── HTTP client singleton ─────────────────────────────────────────────────────

@st.cache_resource
def _headers() -> dict:
    key = st.secrets["SUPABASE_ANON_KEY"]
    return {
        "apikey":        key,
        "Authorization": f"Bearer {key}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation",
    }

@st.cache_resource
def _base_url() -> str:
    url = st.secrets["SUPABASE_URL"].rstrip("/")
    return f"{url}/rest/v1"

def _get(path: str, params: dict | None = None) -> list:
    r = httpx.get(f"{_base_url()}/{path}", headers=_headers(), params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def _post(path: str, data: dict | list) -> list:
    r = httpx.post(f"{_base_url()}/{path}", headers=_headers(), json=data, timeout=10)
    r.raise_for_status()
    return r.json()

def _patch(path: str, data: dict, params: dict) -> list:
    r = httpx.patch(f"{_base_url()}/{path}", headers=_headers(), json=data, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def _delete(path: str, params: dict) -> None:
    r = httpx.delete(f"{_base_url()}/{path}", headers=_headers(), params=params, timeout=10)
    r.raise_for_status()

def _upsert(path: str, data: dict | list) -> list:
    h = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
    r = httpx.post(f"{_base_url()}/{path}", headers=h, json=data, timeout=10)
    r.raise_for_status()
    return r.json()


# ── Watchlist CRUD ────────────────────────────────────────────────────────────

def load_watchlist() -> list[dict]:
    """Return all watchlist rows ordered by rank."""
    return _get("watchlist", params={"select": "*", "order": "rank.asc"})


def upsert_ticker(
    ticker:     str,
    name:       str,
    sector:     str,
    rank:       int,
    ocf_score:  int   = 50,
    debt_score: int   = 50,
    ocf_label:  str   = "—",
    debt_label: str   = "—",
    de_ratio:   float = 0.0,
    notes:      str   = "",
) -> None:
    _upsert("watchlist", {
        "ticker":     ticker.upper().strip(),
        "name":       name.strip(),
        "sector":     sector.strip(),
        "rank":       rank,
        "ocf_score":  max(0, min(100, ocf_score)),
        "debt_score": max(0, min(100, debt_score)),
        "ocf_label":  ocf_label,
        "debt_label": debt_label,
        "de_ratio":   de_ratio,
        "notes":      notes,
    })


def delete_ticker(ticker: str) -> None:
    t = ticker.upper()
    _delete("entries",   params={"ticker": f"eq.{t}"})
    _delete("watchlist", params={"ticker": f"eq.{t}"})


def reorder_watchlist(ordered_tickers: list[str]) -> None:
    for i, ticker in enumerate(ordered_tickers, start=1):
        _patch("watchlist", data={"rank": i}, params={"ticker": f"eq.{ticker}"})


# ── Entry prices CRUD ─────────────────────────────────────────────────────────

def load_entries() -> dict[str, Optional[float]]:
    rows = _get("entries", params={"select": "ticker,entry_price"})
    return {r["ticker"]: r["entry_price"] for r in rows}


def set_entry(ticker: str, price: Optional[float]) -> None:
    t = ticker.upper()
    if price and price > 0:
        _upsert("entries", {"ticker": t, "entry_price": round(price, 4)})
    else:
        _delete("entries", params={"ticker": f"eq.{t}"})


def set_entries_bulk(entries: dict[str, Optional[float]]) -> None:
    for ticker, price in entries.items():
        set_entry(ticker, price)


# ── Seed helper ───────────────────────────────────────────────────────────────

DEFAULT_WATCHLIST = [
    dict(ticker="NVDA", name="NVIDIA Corporation",         sector="Semiconductors", rank=1,  ocf_score=100, debt_score=96,  ocf_label="$64.1B",    debt_label="~$8.5B",  de_ratio=0.10, notes="Dominant OCF; minimal leverage"),
    dict(ticker="AVGO", name="Broadcom Inc.",              sector="Semiconductors", rank=2,  ocf_score=87,  debt_score=72,  ocf_label="$26.9B FCF", debt_label="$63.8B",  de_ratio=0.80, notes="RSI 84 OB; wait for pullback"),
    dict(ticker="TSM",  name="Taiwan Semiconductor Mfg.", sector="Semiconductors", rank=3,  ocf_score=83,  debt_score=92,  ocf_label="NT$2,275B",  debt_label="NT$896B", de_ratio=0.18, notes="GeoPol risk; strong OCF cover"),
    dict(ticker="ANET", name="Arista Networks",            sector="Networking",     rank=4,  ocf_score=67,  debt_score=100, ocf_label="$4.3B FCF",  debt_label="$0",      de_ratio=0.00, notes="Zero debt; oversold bounce setup"),
    dict(ticker="APH",  name="Amphenol Corp.",             sector="Components",     rank=5,  ocf_score=66,  debt_score=55,  ocf_label="$4.4B FCF",  debt_label="$14.6B",  de_ratio=0.75, notes="FCF doubled YoY; neutral RSI"),
    dict(ticker="MU",   name="Micron Technology",          sector="Memory",         rank=6,  ocf_score=63,  debt_score=50,  ocf_label="Strong",     debt_label="$15.0B",  de_ratio=0.45, notes="MACD +18.62; memory crunch play"),
    dict(ticker="SNDK", name="SanDisk Corp.",              sector="Storage",        rank=7,  ocf_score=58,  debt_score=80,  ocf_label="$1.5B H1",   debt_label="$583M",   de_ratio=0.15, notes="RSI 80 OB; wait for pullback"),
    dict(ticker="VRT",  name="Vertiv Holdings",            sector="Infrastructure", rank=8,  ocf_score=55,  debt_score=62,  ocf_label="$2.1B",      debt_label="$2.9B",   de_ratio=0.74, notes="Interest cover 21.3x; DC power play"),
    dict(ticker="WDC",  name="Western Digital",            sector="Storage",        rank=9,  ocf_score=48,  debt_score=44,  ocf_label="Positive",   debt_label="Moderate",de_ratio=0.60, notes="HDD oligopoly; higher debt"),
    dict(ticker="EME",  name="EMCOR Group",                sector="Construction",   rank=10, ocf_score=42,  debt_score=76,  ocf_label="Steady",     debt_label="Low",     de_ratio=0.20, notes="Defensive DC construction exposure"),
]


def seed_defaults_if_empty() -> None:
    """Only seeds if watchlist table is empty — safe to call on every startup."""
    existing = load_watchlist()
    if not existing:
        for row in DEFAULT_WATCHLIST:
            _upsert("watchlist", row)
