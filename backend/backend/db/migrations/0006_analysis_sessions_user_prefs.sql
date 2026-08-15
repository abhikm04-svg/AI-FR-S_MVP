-- Consolidates session config into a single user_prefs JSONB column instead
-- of separate risk_profile/instruments columns. The original 0003 migration
-- didn't anticipate needing target_return/horizon/capital to fully
-- reconstruct a UserPrefs for resuming/re-triggering a run; storing the
-- whole thing as one JSONB blob avoids repeating this gap for the next
-- field someone adds to the profile form.
--
-- Table has no production data yet (Phase 1 predates any real usage), so
-- this is a clean schema adjustment, not a data migration.

ALTER TABLE analysis_sessions
    ADD COLUMN IF NOT EXISTS user_prefs JSONB;

ALTER TABLE analysis_sessions
    DROP COLUMN IF EXISTS risk_profile,
    DROP COLUMN IF EXISTS instruments;
