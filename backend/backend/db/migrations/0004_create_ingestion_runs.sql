-- Visibility into ingestion failures (Phase 2). Replaces ingest_data.py's
-- print()-only error handling, which is invisible outside a GitHub Actions
-- log tail.

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running',
    total_schemes INT,
    succeeded     INT,
    failed        INT,
    failed_codes  JSONB DEFAULT '[]'::jsonb
);
