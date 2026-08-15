-- Normalized, row-per-day replacement for the mf_nav_history JSON-blob table.
-- Enables the batched multi-scheme read that fixes the N+1 query bug:
--   WHERE scheme_code = ANY($1) AND nav_date >= $2
-- in a single round trip, plus delta-only ingestion writes (only new
-- (scheme_code, nav_date) rows get inserted on each ingestion run, instead of
-- rewriting the entire per-scheme JSON blob every time).

CREATE TABLE IF NOT EXISTS mf_nav_prices (
    scheme_code TEXT NOT NULL REFERENCES mf_schemes(scheme_code) ON DELETE CASCADE,
    nav_date    DATE NOT NULL,
    nav         NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (scheme_code, nav_date)
);

-- No extra index: the PK's btree index already has scheme_code as its leading
-- column, which serves the batched-read query pattern above directly.
