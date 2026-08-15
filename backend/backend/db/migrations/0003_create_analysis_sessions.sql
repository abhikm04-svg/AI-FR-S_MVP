-- Query-friendly session metadata for the "list my past runs" UI (Phase 4).
-- LangGraph's AsyncPostgresSaver checkpoint tables (added separately, in Phase 3,
-- via saver.setup()) store opaque state blobs keyed by thread_id with no
-- user_id/status/created_at index suitable for a history-list query -- this
-- table is that index; the checkpointer remains the source of truth for full
-- graph state.

CREATE TABLE IF NOT EXISTS analysis_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id     TEXT NOT NULL UNIQUE,
    user_id       TEXT NOT NULL,
    goal          TEXT,
    risk_profile  JSONB,
    instruments   JSONB,
    status        TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analysis_sessions_user
    ON analysis_sessions (user_id, created_at DESC);
