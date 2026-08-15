-- One-off backfill from the old JSON-blob mf_nav_history table into the new
-- normalized mf_nav_prices table. Pure SQL (not row-by-row Python) to avoid
-- recreating the same N+1 problem during the migration itself.
--
-- Date format (DD-MM-YYYY) confirmed from ingest_data.py's fetch_and_save_nav,
-- which stores mftool's native AMFI date format as-is.
--
-- Regex guards on date/nav shape are defensive: the two existing Streamlit
-- copies parse MF dates inconsistently (Application/app.py uses
-- errors='coerce', Multi Page Test/shared_lib.py does not), which is direct
-- evidence the source data isn't guaranteed uniform. A malformed row here
-- should be skipped, not abort the whole backfill.
--
-- Safe to re-run: ON CONFLICT DO NOTHING makes this idempotent.
-- Does NOT touch or drop mf_nav_history -- kept read-only until Phase 5 cleanup.

INSERT INTO mf_nav_prices (scheme_code, nav_date, nav)
SELECT h.scheme_code,
       to_date(elem->>'date', 'DD-MM-YYYY'),
       (elem->>'nav')::numeric
FROM mf_nav_history h,
     jsonb_array_elements(h.history::jsonb) elem
WHERE elem->>'date' ~ '^\d{2}-\d{2}-\d{4}$'
  AND elem->>'nav' ~ '^[0-9]+(\.[0-9]+)?$'
ON CONFLICT (scheme_code, nav_date) DO NOTHING;

-- Populate the denormalized "latest NAV" cache on mf_schemes from the now-backfilled data.
UPDATE mf_schemes s
SET last_nav       = p.nav,
    last_nav_date  = p.nav_date,
    last_synced_at = now()
FROM (
    SELECT DISTINCT ON (scheme_code) scheme_code, nav_date, nav
    FROM mf_nav_prices
    ORDER BY scheme_code, nav_date DESC
) p
WHERE s.scheme_code = p.scheme_code;
