"""
pages/1_Admin.py
Watchlist admin UI — add, edit, delete, and reorder tickers.
All changes persist to Supabase immediately.
"""

import streamlit as st
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import db

st.set_page_config(
    page_title="Watchlist Admin",
    page_icon="🛠️",
    layout="wide",
)

# ── Auth gate — simple password via st.secrets ────────────────────────────────
def check_auth() -> bool:
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "")
    if not admin_pw:
        return True  # No password set → open access (dev mode)
    if st.session_state.get("admin_authed"):
        return True
    with st.form("auth_form"):
        st.markdown("### 🔒 Admin login")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Unlock"):
            if pw == admin_pw:
                st.session_state["admin_authed"] = True
                st.rerun()
            else:
                st.error("Incorrect password")
    return False

if not check_auth():
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🛠️ Watchlist Admin")
st.caption("All changes are written to Supabase immediately and reflected in the dashboard.")
st.page_link("app.py", label="← Back to dashboard")
st.divider()

# ── Load current watchlist ────────────────────────────────────────────────────
@st.cache_data(ttl=5)
def load_wl():
    return db.load_watchlist()

rows = load_wl()

# ── Helper: validate ticker via yfinance ─────────────────────────────────────
def validate_ticker(ticker: str) -> tuple[bool, str]:
    """Return (valid, company_name_or_error)."""
    try:
        info = yf.Ticker(ticker).fast_info
        name = getattr(info, "long_name", None) or ticker
        price = getattr(info, "last_price", None)
        if price is None:
            return False, "Ticker not found or no price data"
        return True, name
    except Exception as e:
        return False, str(e)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Current watchlist with inline editing
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## Current watchlist")
st.caption("Edit any field inline, then click **Save** on that row. Delete removes from dashboard immediately.")

if not rows:
    st.info("Watchlist is empty. Add a ticker below.")
else:
    # Column headers
    hcols = st.columns([0.5, 1, 2.5, 1.5, 0.8, 0.8, 1.2, 1.2, 0.7, 2.5, 0.8])
    for col, label in zip(hcols, ["Rank", "Ticker", "Company", "Sector",
                                   "OCF%", "Debt%", "OCF (ann.)", "LT Debt",
                                   "D/E", "Notes", "Actions"]):
        col.markdown(f"**{label}**")
    st.divider()

    for row in rows:
        t = row["ticker"]
        key = f"edit_{t}"

        with st.container():
            cols = st.columns([0.5, 1, 2.5, 1.5, 0.8, 0.8, 1.2, 1.2, 0.7, 2.5, 0.8])
            new_rank        = cols[0].number_input("", value=int(row["rank"]),   min_value=1, max_value=999, key=f"{key}_rank",       label_visibility="collapsed")
            cols[1].markdown(f"**{t}**")
            new_name        = cols[2].text_input("", value=row["name"],           key=f"{key}_name",       label_visibility="collapsed")
            new_sector      = cols[3].text_input("", value=row["sector"],         key=f"{key}_sector",     label_visibility="collapsed")
            new_ocf_score   = cols[4].number_input("", value=int(row["ocf_score"]),  min_value=0, max_value=100, key=f"{key}_ocf",   label_visibility="collapsed")
            new_debt_score  = cols[5].number_input("", value=int(row["debt_score"]), min_value=0, max_value=100, key=f"{key}_debt",  label_visibility="collapsed")
            new_ocf_label   = cols[6].text_input("", value=row["ocf_label"],     key=f"{key}_ocfl",       label_visibility="collapsed")
            new_debt_label  = cols[7].text_input("", value=row["debt_label"],    key=f"{key}_debtl",      label_visibility="collapsed")
            new_de          = cols[8].number_input("", value=float(row["de_ratio"]), min_value=0.0, step=0.01, format="%.2f", key=f"{key}_de", label_visibility="collapsed")
            new_notes       = cols[9].text_input("", value=row.get("notes",""), key=f"{key}_notes",       label_visibility="collapsed")

            with cols[10]:
                btn_save, btn_del = st.columns(2)
                if btn_save.button("💾", key=f"{key}_save", help="Save changes"):
                    db.upsert_ticker(
                        ticker=t, name=new_name, sector=new_sector,
                        rank=new_rank, ocf_score=new_ocf_score,
                        debt_score=new_debt_score, ocf_label=new_ocf_label,
                        debt_label=new_debt_label, de_ratio=new_de,
                        notes=new_notes,
                    )
                    st.cache_data.clear()
                    st.success(f"{t} saved ✓")
                    st.rerun()

                if btn_del.button("🗑️", key=f"{key}_del", help=f"Delete {t}",
                                  type="secondary"):
                    st.session_state[f"confirm_del_{t}"] = True

            # Confirm-delete modal
            if st.session_state.get(f"confirm_del_{t}"):
                st.warning(
                    f"⚠️ Delete **{t}** from watchlist? This will also remove its entry price.",
                    icon="⚠️",
                )
                ca, cb, _ = st.columns([1, 1, 5])
                if ca.button("Yes, delete", key=f"confirm_yes_{t}", type="primary"):
                    db.delete_ticker(t)
                    st.cache_data.clear()
                    st.session_state.pop(f"confirm_del_{t}", None)
                    st.success(f"{t} deleted.")
                    st.rerun()
                if cb.button("Cancel", key=f"confirm_no_{t}"):
                    st.session_state.pop(f"confirm_del_{t}", None)
                    st.rerun()

        st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Add new ticker
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## Add new ticker")
st.caption("Enter a Yahoo Finance ticker. The company name will be auto-fetched.")

with st.form("add_ticker_form", clear_on_submit=True):
    a1, a2, a3, a4 = st.columns([1, 2.5, 1.5, 1])
    new_ticker  = a1.text_input("Ticker *", placeholder="e.g. SMCI")
    new_name    = a2.text_input("Company name", placeholder="Auto-filled if blank")
    new_sector  = a3.text_input("Sector", placeholder="e.g. Semiconductors")
    new_rank    = a4.number_input("Rank", min_value=1, max_value=999,
                                  value=(max(r["rank"] for r in rows) + 1) if rows else 1)

    b1, b2, b3, b4, b5 = st.columns(5)
    new_ocf_score  = b1.number_input("OCF score (0–100)", 0, 100, 50)
    new_debt_score = b2.number_input("Debt score (0–100)", 0, 100, 50)
    new_ocf_label  = b3.text_input("OCF label", placeholder="e.g. $2.1B")
    new_debt_label = b4.text_input("LT Debt label", placeholder="e.g. $1.5B")
    new_de_ratio   = b5.number_input("D/E ratio", 0.0, step=0.01, format="%.2f")

    new_notes = st.text_input("Notes (optional)", placeholder="e.g. Overbought RSI; wait for pullback")

    submitted = st.form_submit_button("➕ Add to watchlist", type="primary", use_container_width=True)

    if submitted:
        ticker_clean = new_ticker.strip().upper()
        if not ticker_clean:
            st.error("Ticker is required.")
        elif ticker_clean in {r["ticker"] for r in rows}:
            st.error(f"{ticker_clean} is already in the watchlist.")
        else:
            with st.spinner(f"Validating {ticker_clean} on Yahoo Finance…"):
                valid, fetched_name = validate_ticker(ticker_clean)

            if not valid:
                st.error(f"Could not validate {ticker_clean}: {fetched_name}")
            else:
                final_name = new_name.strip() or fetched_name
                db.upsert_ticker(
                    ticker=ticker_clean, name=final_name,
                    sector=new_sector.strip(), rank=new_rank,
                    ocf_score=new_ocf_score, debt_score=new_debt_score,
                    ocf_label=new_ocf_label or "—",
                    debt_label=new_debt_label or "—",
                    de_ratio=new_de_ratio, notes=new_notes,
                )
                st.cache_data.clear()
                st.success(f"✅ {ticker_clean} ({final_name}) added to watchlist!")
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Bulk re-rank
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## Re-rank watchlist")
st.caption("Drag-free re-ranking: paste tickers in desired order, one per line.")

current_order = "\n".join(r["ticker"] for r in rows)
new_order_raw = st.text_area(
    "Ticker order (one per line)",
    value=current_order,
    height=220,
    help="Reorder tickers by editing this list. Each ticker must already exist in the watchlist.",
)

if st.button("🔃 Apply new rank order", type="primary"):
    new_order = [t.strip().upper() for t in new_order_raw.strip().splitlines() if t.strip()]
    existing  = {r["ticker"] for r in rows}
    invalid   = [t for t in new_order if t not in existing]
    dupes     = [t for t in new_order if new_order.count(t) > 1]

    if invalid:
        st.error(f"Unknown tickers (not in watchlist): {', '.join(invalid)}")
    elif dupes:
        st.error(f"Duplicate tickers: {', '.join(set(dupes))}")
    elif set(new_order) != existing:
        missing = existing - set(new_order)
        st.error(f"Missing tickers from list: {', '.join(missing)}")
    else:
        db.reorder_watchlist(new_order)
        st.cache_data.clear()
        st.success("Rank order updated ✓")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Bulk import via CSV paste
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📋 Bulk import (CSV paste)", expanded=False):
    st.caption(
        "Paste CSV rows — header required: "
        "`ticker,name,sector,rank,ocf_score,debt_score,ocf_label,debt_label,de_ratio,notes`  \n"
        "Existing tickers will be updated (upsert). Unknown tickers are validated via Yahoo Finance."
    )
    csv_input = st.text_area("Paste CSV here", height=160,
                              placeholder="ticker,name,sector,rank,...\nNVDA,NVIDIA Corp,Semiconductors,1,100,96,...\n")
    if st.button("📥 Import CSV rows"):
        import io, csv
        try:
            reader = csv.DictReader(io.StringIO(csv_input.strip()))
            required = {"ticker", "name", "sector", "rank"}
            rows_in  = list(reader)
            if not rows_in:
                st.error("No rows found.")
            elif not required.issubset(set(reader.fieldnames or [])):
                st.error(f"Missing required columns: {required - set(reader.fieldnames or [])}")
            else:
                errors, imported = [], 0
                prog = st.progress(0)
                for i, r in enumerate(rows_in):
                    t = r["ticker"].strip().upper()
                    try:
                        db.upsert_ticker(
                            ticker=t,
                            name=r.get("name","").strip(),
                            sector=r.get("sector","").strip(),
                            rank=int(r.get("rank", 99)),
                            ocf_score=int(r.get("ocf_score", 50)),
                            debt_score=int(r.get("debt_score", 50)),
                            ocf_label=r.get("ocf_label","—"),
                            debt_label=r.get("debt_label","—"),
                            de_ratio=float(r.get("de_ratio", 0)),
                            notes=r.get("notes",""),
                        )
                        imported += 1
                    except Exception as e:
                        errors.append(f"{t}: {e}")
                    prog.progress((i + 1) / len(rows_in))

                st.cache_data.clear()
                st.success(f"Imported {imported} rows.")
                if errors:
                    st.warning("Errors: " + "; ".join(errors))
                st.rerun()
        except Exception as e:
            st.error(f"CSV parse error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Danger zone
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("☠️ Danger zone", expanded=False):
    st.error(
        "**Reset watchlist** — deletes all tickers and entries from Supabase, "
        "then re-seeds the original 10 AI infrastructure names."
    )
    confirm_reset = st.text_input(
        "Type **RESET** to confirm",
        placeholder="RESET",
    )
    if st.button("🔴 Reset to defaults", type="primary"):
        if confirm_reset.strip() == "RESET":
            client = db.get_client()
            client.table("entries").delete().neq("ticker", "").execute()
            client.table("watchlist").delete().neq("ticker", "").execute()
            for row in db.DEFAULT_WATCHLIST:
                client.table("watchlist").upsert(row, on_conflict="ticker").execute()
            st.cache_data.clear()
            st.success("Watchlist reset to defaults ✓")
            st.rerun()
        else:
            st.error("Type RESET (all caps) to confirm.")
