-- Extends the existing mf_schemes table (created ad hoc via supabase-py .upsert()
-- calls, never captured in a migration) with columns needed for delta-sync
-- ingestion and a denormalized "latest NAV" cache. Uses ADD COLUMN IF NOT EXISTS
-- since the live table's exact origin is undocumented, and does not touch the
-- existing `last_updated` column -- the old Streamlit app and ingest_data.py
-- still read/write it until the Phase 5 cutover. New code should use
-- last_synced_at instead.

ALTER TABLE mf_schemes
    ADD COLUMN IF NOT EXISTS is_direct_growth BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS last_nav NUMERIC(12,4),
    ADD COLUMN IF NOT EXISTS last_nav_date DATE,
    ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
