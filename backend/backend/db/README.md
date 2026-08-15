# Phase 1 — Schema + backfill

SQL migrations for the schema redesign described in `plan1.md` §2. These fix the
two root causes of the "10+ minutes to fetch the full dataset" bug:

- `mf_nav_history` stores each scheme's entire NAV history as one JSON blob,
  forcing a query per scheme code to read it (`migrations/0002` replaces this
  with a normalized `mf_nav_prices` table that supports a single batched read
  across all scheme codes at once).
- Ingestion rewrites that whole blob every run instead of writing only new
  rows (fixed in Phase 2, once this schema exists).

## What's here

- `migrations/0001_extend_mf_schemes.sql` — adds columns to the existing live
  `mf_schemes` table (delta-sync tracking + a denormalized latest-NAV cache).
- `migrations/0002_create_mf_nav_prices.sql` — the new row-per-day NAV table.
- `migrations/0003_create_analysis_sessions.sql` — session metadata table for
  Phase 3/4 (LangGraph persisted sessions, "list my past runs" UI).
- `migrations/0004_create_ingestion_runs.sql` — ingestion failure tracking for
  Phase 2.
- `migrations/0005_backfill_mf_nav_history.sql` — one-off backfill of existing
  `mf_nav_history` blobs into `mf_nav_prices`. Idempotent (`ON CONFLICT DO
  NOTHING`), safe to re-run. Does **not** touch or drop `mf_nav_history`.
- `verify_backfill.sql` — ad hoc spot-check query, not part of the migration
  sequence. Run manually after 0005.
- `apply_migrations.py` — standalone runner (needs `asyncpg`; not yet added
  anywhere else in the repo since the full `backend/` package is Phase 3).

## How to apply

You need the **direct Postgres connection string** for your Supabase project
(Project Settings → Database → Connection string) — not the `SUPABASE_URL`/
anon-key REST pair used by the existing Streamlit apps. Pick one:

**Option A — Supabase SQL Editor (no local setup)**
Paste each file's contents into the SQL Editor in order (0001 → 0005), run
each one, then run `verify_backfill.sql` separately to check the backfill.

**Option B — Supabase CLI**, if you have it installed:
```
supabase db push
```
(requires the project linked via `supabase link`; not set up in this repo yet)

**Option C — `apply_migrations.py`**, from this directory:
```
pip install asyncpg
python apply_migrations.py --dsn "postgresql://...your Supabase DB URL..."
# or: set SUPABASE_DB_URL then run without --dsn
```
Tracks applied migrations in a `schema_migrations` table so it's safe to
re-run — only unapplied files execute. Use `--dry-run` to preview.

## After applying

Run `verify_backfill.sql`. It should return **zero rows**. Any row returned
is either a real gap (investigate) or one of the malformed entries the
backfill's regex guards intentionally skip (spot-check a few against the raw
`mf_nav_history.history` blob to tell which).

Leave `mf_nav_history` in place, read-only, until the Phase 5 cutover.
