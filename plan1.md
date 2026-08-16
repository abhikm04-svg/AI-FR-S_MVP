# FinAgents India — Full Rewrite Plan (Streamlit → React + FastAPI + LangGraph)

## Context

The app currently exists as two duplicated, drifting Streamlit implementations
(`Application/app.py` and `Multi Page Test/`) of the same three-stage "agent" pipeline
(Researcher → Analyst → Business Analyst), hand-rolled as plain Python classes rather than
a real orchestration framework. Two concrete problems are driving this rewrite:

1. **Performance**: fetching the full mutual-fund dataset takes 10+ minutes. Root cause,
   confirmed by reading the code: `FinancialTools.fetch_market_data()`
   (`Application/app.py:426-473`, `Multi Page Test/shared_lib.py:301-333`) loops over every
   MF scheme code and issues **one Supabase query per code**
   (`.table("mf_nav_history").select("history").eq("scheme_code", code)`) — a strict N+1
   pattern across thousands of schemes. The underlying `mf_nav_history` table also stores
   each scheme's entire history as a single JSON blob, so the daily ingestion job
   (`ingest_data.py`) rewrites that whole blob every run instead of writing only new rows,
   and does two separate writes per scheme (blob upsert + a separate `last_updated` update).
2. **Architecture drift**: the two Streamlit copies have already diverged in ways that produce
   different behavior (e.g. `Application/app.py` parses MF dates defensively with
   `errors='coerce'`; `Multi Page Test/shared_lib.py` doesn't, and will raise on a malformed
   date). There's no real LangChain/LangGraph orchestration despite the "agent" framing — only
   the reporter step actually calls an LLM.

**Also found during research, independent of the above**: both `.streamlit/secrets.toml` files
(containing real `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`) are committed to git, and no
`.gitignore` has ever existed in this repo. This is a live credential leak and must be fixed
first, regardless of the rewrite timeline.

**Target stack** (confirmed with user): React (Vite) frontend in `UI/`, Python/FastAPI backend
in `backend/`, LangGraph for agent orchestration with Postgres-checkpointed persisted sessions,
Supabase (Postgres) as the database with a redesigned schema, same underlying data sources
(mftool/AMFI, nselib, yfinance) but a redesigned ingestion strategy. Full replacement of the
Streamlit apps (removed once the new stack reaches parity — not deleted immediately). Tests live
next to the files they test, no separate `tests/` tree.

**Decisions confirmed with user**:
- User identity: anonymous per-browser UUID (`localStorage`, sent as a request header) — no
  login screen for v1.
- Deployment: single long-lived backend instance — justifies in-process `asyncio` background
  tasks instead of a Celery/Redis task queue.
- NSE equity/ETF universe caching (the bhavcopy re-scan on every run) — **deferred**, out of
  scope for this rewrite.
- Charting: **Recharts** (not Plotly.js) — React-native, lighter bundle, easier to theme against
  the existing oklch CSS tokens.

---

## 0. Security fix (do first, independent of everything else)

- Rotate `GEMINI_API_KEY` and both Supabase keys in their dashboards — this is the step that
  actually neutralizes the leak; adding `.gitignore` alone does not remove keys already in git
  history.
- Add root `.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `**/secrets.toml`, `.env`, `.env.*`
  (except `.env.example`), `UI/node_modules/`, `UI/dist/`, `.DS_Store`.
- `git rm --cached` both `.streamlit/secrets.toml` files; add `.env.example` files describing the
  required keys with no real values.
- Done when: new keys are live, old keys revoked at the provider, no plaintext secret file is
  tracked going forward.

---

## 1. Backend layout (`backend/`)

FastAPI (async, `uvicorn`). Synchronous libraries being kept (`yfinance`, `mftool`, `nselib`) are
wrapped in `asyncio.to_thread(...)` at call sites so they never block the event loop.

```
backend/
  pyproject.toml               # single dependency manifest (uv recommended), replaces the
                                #   three drifted requirements.txt files
  .env.example
  backend/
    core/
      config.py                # pydantic-settings: SUPABASE_URL, SUPABASE_DB_URL (raw PG DSN),
                                #   GEMINI_API_KEY — replaces the st.secrets/os.getenv dual path
    db/
      connection.py             # asyncpg pool factory
      migrations/
        0001_init_reference_data.sql
        0002_mf_nav_prices.sql
        0003_analysis_sessions.sql
        0004_ingestion_runs.sql
        0005_backfill_mf_nav_history.sql
    data/
      market_data.py            # THE single canonical replacement for FinancialTools —
                                 #   consolidates the two drifted copies. No Streamlit imports.
      test_market_data.py
      mftool_client.py          # RobustMftool, ported as-is (the AMFI malformed-line defense
                                 #   is a good, minimal fix — keep it)
      test_mftool_client.py
      models.py                 # AssetRef, AssetMetrics (Pydantic)
    repository/
      schemes.py                 # mf_schemes queries
      nav_prices.py               # batched NAV read (§2) + delta-write helpers — this is where
                                   #   the N+1 fix lives
      sessions.py                  # analysis_sessions CRUD
      test_schemes.py / test_nav_prices.py / test_sessions.py
    ingestion/
      schemes.py
      nav_history.py              # delta-sync fetch/write (§3)
      failures.py                  # ingestion_runs helpers
      run.py                        # CLI entrypoint invoked by the GitHub Action
      test_*.py colocated
    agents/
      state.py                    # AgentState TypedDict
      graph.py                     # StateGraph wiring + checkpointer setup
      prompts.py
      nodes/
        researcher.py
        analyst.py
        reporter.py
        test_*.py colocated
    api/
      main.py                      # FastAPI app factory, CORS, startup (checkpointer.setup())
      deps.py                       # DI: db pool, checkpointer, LLM client
      routes/
        sessions.py                 # POST/GET /api/sessions, .../run, .../stream
        test_sessions.py
```

**Why this split**: `data/` and `repository/` are Streamlit-free and independently testable;
`agents/` nodes stay thin, calling into that tested service layer instead of embedding
fetch/compute logic inline — this is exactly what let the two Streamlit copies drift apart.

**Deliberately not doing**: no Celery/Redis (single-instance deployment confirmed), no
SQLAlchemy/Alembic ORM (the whole point of the fix is a handful of hand-tunable batch queries —
plain SQL migrations run via the Supabase CLI, executed with `asyncpg`, keeps the batching
visible), no LLM/agentic behavior added to the researcher/analyst nodes (they're deterministic
today — fetch, compute Sharpe/volatility/SMA, filter — and should stay plain Python functions in
the graph; only the reporter node touches an LLM).

---

## 2. Supabase schema redesign — the core fix

Replace the blob-per-scheme `mf_nav_history` with a tidy, row-per-day table:

```sql
CREATE TABLE mf_schemes (
    scheme_code      TEXT PRIMARY KEY,
    scheme_name      TEXT NOT NULL,
    is_direct_growth BOOLEAN NOT NULL DEFAULT TRUE,
    last_nav         NUMERIC(12,4),
    last_nav_date    DATE,
    last_synced_at   TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mf_nav_prices (
    scheme_code TEXT NOT NULL REFERENCES mf_schemes(scheme_code) ON DELETE CASCADE,
    nav_date    DATE NOT NULL,
    nav         NUMERIC(12,4) NOT NULL,
    PRIMARY KEY (scheme_code, nav_date)
    -- the PK's btree index (scheme_code leading) already serves the batched read below;
    -- no extra index needed
);

CREATE TABLE analysis_sessions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id     TEXT NOT NULL UNIQUE,   -- 1:1 with the LangGraph checkpointer thread_id
    user_id       TEXT NOT NULL,          -- the anonymous browser UUID
    goal          TEXT,
    risk_profile  JSONB,
    instruments   JSONB,
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending|running|completed|failed
    error_message TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_analysis_sessions_user ON analysis_sessions (user_id, created_at DESC);

CREATE TABLE ingestion_runs (
    id            BIGSERIAL PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running',
    total_schemes INT, succeeded INT, failed INT,
    failed_codes  JSONB DEFAULT '[]'::jsonb   -- [{code, error, at}, ...]
);
```

`analysis_sessions` is necessary, not optional: LangGraph's `AsyncPostgresSaver` creates its own
`checkpoints`/`checkpoint_blobs`/`checkpoint_writes` tables with no `user_id`/`status`/indexed
`created_at` — unsuitable for a "list my past runs" query. `analysis_sessions` is the
query-friendly index; the checkpointer remains the source of truth for full graph state.

**The batched-read fix that replaces the N+1 loop** — run directly over the backend's own
`asyncpg` pool (the backend already needs a direct Postgres connection for the LangGraph
checkpointer, so there's no reason to also go through PostgREST for this):

```python
rows = await conn.fetch(
    "SELECT scheme_code, nav_date, nav FROM mf_nav_prices "
    "WHERE scheme_code = ANY($1::text[]) AND nav_date >= $2 ORDER BY scheme_code, nav_date",
    codes, since_date,
)
```

One round trip for the entire universe instead of one per scheme code.

**Backfill** (one-off, pure SQL — not row-by-row Python, to avoid re-creating the same N+1
problem during migration):

```sql
INSERT INTO mf_nav_prices (scheme_code, nav_date, nav)
SELECT h.scheme_code,
       to_date(elem->>'date', 'DD-MM-YYYY'),
       (elem->>'nav')::numeric
FROM mf_nav_history h, jsonb_array_elements(h.history::jsonb) elem
WHERE elem->>'date' IS NOT NULL AND elem->>'nav' IS NOT NULL
ON CONFLICT (scheme_code, nav_date) DO NOTHING;
```

(Date format `DD-MM-YYYY` confirmed from `ingest_data.py`'s `fetch_and_save_nav`.) After
backfilling, populate `mf_schemes.last_nav`/`last_nav_date`/`last_synced_at` from
`MAX(nav_date)` per scheme, spot-check row counts against the old blob table, then leave
`mf_nav_history` in place read-only until Phase 5 cleanup (don't drop it in the same phase you
migrate).

---

## 3. Ingestion pipeline redesign (`backend/ingestion/`)

Same data sources (no bulk/"since date" endpoint exists at the mftool/AMFI source, so the
per-scheme fetch call is unavoidable) — what changes is everything after the fetch.

1. `ingest_schemes()` — mostly unchanged: fetch AMFI codes, filter Direct+Growth, batch-upsert
   into `mf_schemes`.
2. **New pre-fetch step**: one query — `SELECT scheme_code, last_nav_date FROM mf_schemes` — to
   know in memory which dates are already stored, before fetching or writing anything.
3. **Fetch phase**: `asyncio.to_thread(mf.get_scheme_historical_nav, code)` per scheme, bounded
   by `asyncio.Semaphore(N)` (start N=20-30, up from today's `ThreadPoolExecutor(max_workers=10)`
   — validate empirically that AMFI doesn't start throttling before committing to a higher
   number), with `tenacity` retry (2-3 attempts, exponential backoff) so transient failures
   aren't permanent misses. Explicitly size the thread pool backing `asyncio.to_thread` (its
   default executor caps around `min(32, cpu_count+4)`) to match the chosen concurrency.
4. **New delta computation** (in-memory, no DB round trip): keep only NAV entries newer than
   that scheme's `last_nav_date` (or the full 5-year window for new schemes). This is the actual
   fix for "full blob rewrite every run" — a healthy scheme contributes ~1 row/day after the
   initial backfill instead of ~1,250.
5. **New batched write phase**: accumulate delta rows across all schemes, then one chunked
   `INSERT ... ON CONFLICT (scheme_code, nav_date) DO NOTHING` into `mf_nav_prices` (safe/pure
   append — published NAVs are immutable), plus one batched multi-row upsert into `mf_schemes`
   setting `last_nav`/`last_nav_date`/`last_synced_at` — replacing both the double-write and the
   per-scheme write count with a small constant number of batched writes.
6. **New failure tracking**: an `ingestion_runs` row per run (`status='running'` at start), a
   `failed_codes` JSONB array of `{code, error, at}` for anything that fails after retries,
   finalized to `completed`/`failed` with counts — replacing the current `print()`-only failure
   handling that's invisible outside a GitHub Actions log tail.
7. `run.py` — CLI entrypoint; `.github/workflows/daily_ingest.yml`'s `run:` step changes from
   `python ingest_data.py` to the new module once Phase 2 cuts over. Schedule/trigger unchanged.

---

## 4. LangGraph design (`backend/agents/`)

**State** (`AgentState` TypedDict): `user_prefs`, `asset_universe` (list of `{ticker, name}`),
`analyzed_metrics` (list of `AssetMetrics` — the reduced technical+fundamental rows, ~20 max),
`final_thesis`, `status`, `error`. Deliberately **excludes raw OHLC/NAV DataFrames** — those are
computed and reduced immediately in the researcher node, not persisted, since
`AsyncPostgresSaver` blobs the entire state at every checkpoint and multi-thousand-row
per-ticker DataFrames would bloat every write. The chart-worthy price history for the final
top-5 picks is re-fetched on demand by the results endpoint via the same batched-read repository
method from §2, not stored per-run.

**Nodes** (linear `researcher → analyst → reporter → END`, with a conditional edge to an error
terminal if `analyzed_metrics` is empty after the analyst step — mirrors today's
`if analysis_results.empty: st.error(...)`):

- `researcher` (plain function, no LLM) — ports `MarketResearcher.execute()`: calls
  `data.get_indian_ticker_suggestions()` + the DB-batched `data.fetch_market_data()`.
- `analyst` (plain function, no LLM) — ports `FinancialAnalyst.execute()`: risk-slab filtering,
  Sharpe-ratio ranking, top-20 selection, fundamentals fetch scoped to the shortlist only (that
  part of the current design — scoping the slow fundamentals call to a small shortlist — is
  already correct, keep it as-is).
- `reporter` (the one real LLM node) — ports `BusinessAnalyst.execute()`'s prompt via
  `ChatGoogleGenerativeAI` (`langchain_google_genai`).

**Checkpointer**: `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver`, pointed at Supabase's
direct Postgres DSN (`SUPABASE_DB_URL`, distinct from the REST `SUPABASE_URL`/key pair used
elsewhere). If ever deployed behind Supabase's pooler, use session-mode (port 5432) or a direct
connection, not the transaction-mode pgbouncer pooler (port 6543) — prepared statements used by
the checkpointer aren't reliable there. (Not a concern for the confirmed single-instance
deployment, noting for future reference.)

**API** (`backend/api/routes/sessions.py`):
- `POST /api/sessions` — creates `analysis_sessions` row + `thread_id`.
- `POST /api/sessions/{id}/run` — starts graph execution as a **detached `asyncio.create_task`**
  (not awaited by the request handler) — this is what makes "close the browser, come back later"
  work.
- `GET /api/sessions/{id}/stream` — SSE endpoint streaming node-completion events.
- `GET /api/sessions/{id}` — reads `analysis_sessions` metadata + `graph.aget_state()` for full
  final state (results page, and resuming/revisiting past runs).
- `GET /api/sessions?user_id=...` — history list, powered entirely by `analysis_sessions`.

---

## 5. React frontend (`UI/`)

Vite + TypeScript, React Router, TanStack Query for server state (session list, session detail,
results), a small `useAnalysisStream` hook wrapping `EventSource` for the one live thing on
screen. No Redux/Zustand — unjustified for this amount of client state. Anonymous UUID identity:
generated client-side on first visit, stored in `localStorage`, sent as a request header.

```
UI/
  package.json / tsconfig.json / vite.config.ts / .env.example
  src/
    main.tsx / App.tsx
    lib/
      theme.ts            # ported oklch design tokens from the current .agent-box/researcher/
                           #   analyst/reporter CSS
      apiClient.ts          # typed fetch wrapper (openapi-typescript against FastAPI's schema)
    routes/
      ProfileSetup.tsx + .test.tsx     # port of Home.py's inputs; POST /api/sessions on submit
      AnalysisRun.tsx + .test.tsx       # live SSE progress view; port of agent-box progress cards
      Results.tsx + .test.tsx            # port of 3_Results.py: thesis, charts, metrics table
      History.tsx + .test.tsx             # NEW — list of past sessions; doesn't exist today,
                                           #   this is the concrete payoff of the checkpointer work
    components/
      AgentProgressCard.tsx + .test.tsx
      PerformanceChart.tsx + .test.tsx    # Recharts line chart (normalized ₹100 growth)
      RiskReturnScatter.tsx + .test.tsx   # Recharts ScatterChart + ZAxis for Sharpe-sized bubbles
      MetricsTable.tsx + .test.tsx
      ThesisReport.tsx + .test.tsx
    hooks/
      useAnalysisStream.ts + .test.ts
      useSessions.ts + .test.ts
    styles/globals.css
```

Before actually building `PerformanceChart.tsx`/`RiskReturnScatter.tsx`, load the `dataviz`
skill for color/legend/accessibility guidance, per standing practice for any new chart code.

---

## 6. Phased execution sequence

1. **Phase 0 — Security** (§0). Done when: keys rotated, `.gitignore` added, secrets untracked.
2. **Phase 1 — Schema + backfill** (§2). Apply migrations, run the SQL backfill, spot-check row
   counts against the old blob table. Done when: new tables verified equivalent; nothing in
   production reads from them yet.
3. **Phase 2 — Ingestion rewrite** (§3). Build `backend/ingestion/`, run alongside the still-live
   `ingest_data.py` for a few days writing to the new tables, diff outputs, then flip
   `daily_ingest.yml` over and retire `ingest_data.py`. Done when: ingestion writes deltas only,
   run time drops materially, failures visible in `ingestion_runs`.
4. **Phase 3 — Backend API + agents** (§1, §4). Build `backend/` end to end with colocated
   tests; validate against the Streamlit app's output for parity on a handful of manual runs.
   Done when: backend fully functional standalone, zero dependency on Streamlit code.
5. **Phase 4 — Frontend** (§5). Build `UI/` against the stable backend API. Done when: full user
   journey (profile → run → results → history) works end-to-end in dev/staging.
6. **Phase 5 — Cutover & cleanup**. Deploy both halves; optionally run old and new in parallel
   briefly; then delete `Application/`, `Multi Page Test/`, root `ingest_data.py`,
   `migrate_mongo_to_supabase.py`, root `requirements.txt`; drop `mf_nav_history` after a
   retention buffer; update `CLAUDE.md` to describe the new architecture.

---

## Verification

- **Phase 1**: `SELECT scheme_code, SUM(jsonb_array_length(history::jsonb)) FROM mf_nav_history GROUP BY scheme_code`
  vs. `SELECT scheme_code, COUNT(*) FROM mf_nav_prices GROUP BY scheme_code` — counts should
  match per scheme (modulo malformed rows the backfill query intentionally skips).
- **Phase 2**: time the new `ingestion/run.py` against the old `ingest_data.py` for a full run;
  confirm `ingestion_runs.failed_codes` populates when a scheme is deliberately made to fail
  (e.g. temporarily invalid code) instead of silently vanishing.
- **Phase 3**: `pytest` across `backend/` (colocated tests); manually invoke
  `POST /api/sessions` → `.../run` → poll `GET /api/sessions/{id}` via curl/Postman and confirm
  `analyzed_metrics`/`final_thesis` are populated and comparable to a same-input Streamlit run;
  time the batched NAV read directly and confirm it's no longer 10+ minutes.
- **Phase 4**: run the full UI journey in a browser (profile → run → watch live progress → view
  results/charts → reload browser mid-run and confirm it resumes via the checkpointer → check
  `/history` lists the completed session).
- **Phase 5**: confirm the app runs with `Application/`, `Multi Page Test/`, and the old
  ingestion script deleted; confirm the GitHub Action still runs green against the new
  `backend/ingestion/run.py` entrypoint.
