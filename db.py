"""
db.py — Supabase persistence layer
Handles watchlist and entry price storage.

Tables required (run supabase_setup.sql to create):
  watchlist   — ticker metadata + fundamental scores
  entries     — per-ticker entry prices
"""

from __future__ import annotations
import os
import streamlit as st
from supabase import create_client, Client
from typing import Optional

# ── Client singleton ──────────────────────────────────────────────────────────

@st.cache_resource
def get_client() -> Client:
    url  = st.secrets["SUPABASE_URL"]
    key  = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


# ── Watchlist CRUD ────────────────────────────────────────────────────────────

def load_watchlist() -> list[dict]:
    """Return all watchlist rows, ordered by rank."""
    client = get_client()
    res = client.table("watchlist").select("*").order("rank").execute()
    return res.data or []


def upsert_ticker(
    ticker:     str,
    name:       str,
    sector:     str,
    rank:       int,
    ocf_score:  int  = 50,
    debt_score: int  = 50,
    ocf_label:  str  = "—",
    debt_label: str  = "—",
    de_ratio:   float = 0.0,
    notes:      str  = "",
) -> None:
    """Insert or update a watchlist row (upsert on ticker)."""
    client = get_client()
    client.table("watchlist").upsert({
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
    }, on_conflict="ticker").execute()


def delete_ticker(ticker: str) -> None:
    """Remove a ticker from watchlist (and cascade-delete its entry)."""
    client = get_client()
    client.table("entries").delete().eq("ticker", ticker.upper()).execute()
    client.table("watchlist").delete().eq("ticker", ticker.upper()).execute()


def reorder_watchlist(ordered_tickers: list[str]) -> None:
    """Update rank column to match the supplied order."""
    client = get_client()
    for i, ticker in enumerate(ordered_tickers, start=1):
        client.table("watchlist").update({"rank": i}).eq("ticker", ticker).execute()


# ── Entry prices CRUD ─────────────────────────────────────────────────────────

def load_entries() -> dict[str, Optional[float]]:
    """Return {ticker: entry_price} for all tickers that have an entry set."""
    client = get_client()
    res = client.table("entries").select("ticker, entry_price").execute()
    return {row["ticker"]: row["entry_price"] for row in (res.data or [])}


def set_entry(ticker: str, price: Optional[float]) -> None:
    """Upsert an entry price for a ticker. Pass None/0 to clear."""
    client = get_client()
    if price and price > 0:
        client.table("entries").upsert(
            {"ticker": ticker.upper(), "entry_price": round(price, 4)},
            on_conflict="ticker"
        ).execute()
    else:
        client.table("entries").delete().eq("ticker", ticker.upper()).execute()


def set_entries_bulk(entries: dict[str, Optional[float]]) -> None:
    """Batch-update entry prices from a {ticker: price} dict."""
    for ticker, price in entries.items():
        set_entry(ticker, price)


# ── Seed helper (first-run only) ──────────────────────────────────────────────

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
    client = get_client()
    existing = client.table("watchlist").select("ticker").execute()
    if not existing.data:
        for row in DEFAULT_WATCHLIST:
            client.table("watchlist").upsert(row, on_conflict="ticker").execute()
