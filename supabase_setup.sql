-- ============================================================
-- AI Infra Dashboard — Supabase Schema
-- Run this once in your Supabase project's SQL Editor
-- ============================================================

-- 1. Watchlist table — stores ticker metadata + fundamental scores
CREATE TABLE IF NOT EXISTS watchlist (
    ticker      TEXT        PRIMARY KEY,
    name        TEXT        NOT NULL,
    sector      TEXT        NOT NULL DEFAULT '',
    rank        INTEGER     NOT NULL DEFAULT 99,
    ocf_score   INTEGER     NOT NULL DEFAULT 50 CHECK (ocf_score BETWEEN 0 AND 100),
    debt_score  INTEGER     NOT NULL DEFAULT 50 CHECK (debt_score BETWEEN 0 AND 100),
    ocf_label   TEXT        NOT NULL DEFAULT '—',
    debt_label  TEXT        NOT NULL DEFAULT '—',
    de_ratio    NUMERIC(6,3) NOT NULL DEFAULT 0,
    notes       TEXT        NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS watchlist_updated_at ON watchlist;
CREATE TRIGGER watchlist_updated_at
    BEFORE UPDATE ON watchlist
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- 2. Entries table — stores per-ticker entry prices
CREATE TABLE IF NOT EXISTS entries (
    ticker      TEXT        PRIMARY KEY REFERENCES watchlist(ticker) ON DELETE CASCADE,
    entry_price NUMERIC(12,4),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS entries_updated_at ON entries;
CREATE TRIGGER entries_updated_at
    BEFORE UPDATE ON entries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- 3. Row Level Security (RLS)
--    Using anon key only — enable RLS but allow all operations from the anon role.
--    For a shared/team deployment, restrict to authenticated users instead.

ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE entries   ENABLE ROW LEVEL SECURITY;

-- Allow full access via anon key (single-user / trusted deployment)
CREATE POLICY "anon full access watchlist"
    ON watchlist FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE POLICY "anon full access entries"
    ON entries   FOR ALL TO anon USING (true) WITH CHECK (true);


-- 4. Useful indexes
CREATE INDEX IF NOT EXISTS watchlist_rank_idx ON watchlist(rank);


-- ============================================================
-- Done. The app will auto-seed DEFAULT_WATCHLIST on first run.
-- ============================================================
