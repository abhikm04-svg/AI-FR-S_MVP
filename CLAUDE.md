# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FinAgents India: a multi-agent workflow (Researcher → Analyst → Business Analyst) that screens Indian
equities, ETFs, and mutual funds and produces an AI-generated investment thesis. Built as:

- `backend/` — Python/FastAPI backend, LangGraph orchestrating the agent pipeline, Supabase (Postgres)
  for data + persisted sessions.
- `UI/` — React (Vite + TypeScript) frontend.

This replaced an earlier pair of duplicated Streamlit apps (see `plan1.md` for the full rewrite
rationale and phased history — the original N+1 query bug that made a full data fetch take 10+ minutes
is what started it).

## Commands

**Backend** (from `backend/`):
```bash
pip install -r requirements.txt
python -m backend.api                 # dev server, http://localhost:8000 (Windows-safe entrypoint —
                                       #   see "Windows event loop" below; plain `uvicorn` CLI works
                                       #   fine on Linux/macOS)
python -m pytest                      # run tests (from backend/, not backend/backend/)
python -m backend.ingestion.run       # run the ingestion pipeline manually; --limit N, --dsn, --concurrency
```

**Frontend** (from `UI/`):
```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # tsc --noEmit && vite build
npm test         # vitest run
```

**Both, via Docker** (from repo root):
```bash
docker compose up --build   # backend :8000, frontend :3000
```
Requires `backend/.env` (see `backend/.env.example`) with `SUPABASE_DB_URL` and `GEMINI_API_KEY`.
**Use the Session Pooler connection string, not the direct `db.<ref>.supabase.co` host** — Supabase's
direct connection is IPv6-only, which fails on networks without IPv6 egress (Docker Desktop's default
network on Windows, some CI runners). Session-mode pooler is IPv4-compatible and still supports
prepared statements, unlike the transaction-mode pooler on port 6543, which the LangGraph checkpointer
needs.

## Architecture

### Package layout

`backend/` (outer, has `requirements.txt`/`Dockerfile`) contains `backend/backend/` (the actual
importable package — `import backend.data.market_data`, etc.). Run commands from the outer `backend/`
directory. Tests live next to the files they test (`test_*.py`), no separate `tests/` tree.

```
backend/backend/
  core/config.py        # pydantic-settings: SUPABASE_DB_URL, GEMINI_API_KEY
  db/
    connection.py        # asyncpg pool factory
    migrations/           # plain SQL, applied via apply_migrations.py (no ORM)
  data/
    market_data.py         # stocks/ETFs via yfinance+nselib; MF price history via the batched
                            #   repository read (NOT a live per-scheme call)
    mftool_client.py        # RobustMftool -- defensive AMFI scheme-code parsing
    models.py                # AssetRef, AssetMetrics, UserPrefs (Pydantic)
  repository/
    nav_prices.py       # THE batched NAV read -- WHERE scheme_code = ANY(...), one round trip
    schemes.py            # mf_schemes reads
    sessions.py             # analysis_sessions CRUD
  ingestion/             # delta-sync pipeline (see below)
  agents/
    state.py               # AgentState TypedDict -- deliberately excludes raw price series
    graph.py                 # StateGraph: researcher -> analyst -> reporter -> END
    nodes/                    # researcher/analyst are plain functions, no LLM; reporter is the
                              #   only node that calls Gemini
  api/
    main.py       # app factory + lifespan (DB pool, checkpointer, compiled graph)
    __main__.py    # dev server entrypoint -- see "Windows event loop" below
    routes/sessions.py   # create/run/stream/detail/history endpoints
```

`UI/src/`: `routes/` (ProfileSetup, AnalysisRun, Results, History), `components/` (charts, tables,
progress cards), `hooks/` (`useSessions`, `useAnalysisStream`), `lib/` (`apiClient`, `theme`,
`agentStates`). Anonymous per-browser UUID identity (`localStorage`, `X-User-Id` header) — no login.

### The agent pipeline (LangGraph)

Linear `researcher → analyst → reporter → END`, with a conditional edge to an error terminal if the
analyst finds nothing matching the user's risk profile. Only the **reporter** node calls an LLM
(`ChatGoogleGenerativeAI`) — researcher and analyst are deterministic data/math, same as before the
rewrite, deliberately kept as plain functions rather than agentic LLM loops.

- **researcher**: builds the candidate asset universe (`data.market_data.get_asset_universe`), fetches
  price history, and reduces it to technical metrics (Sharpe, volatility, SMA trend) *within the same
  node call* — raw price series never get returned into graph state, since the Postgres checkpointer
  blobs the entire state at every checkpoint.
- **analyst**: filters by volatility "risk slab" (`agents/nodes/analyst.py:RISK_SLABS`), ranks by
  Sharpe ratio, takes the top 20, fetches fundamentals (P/E, ROE, etc.) for that shortlist only.
- **reporter**: builds the structured prompt (`agents/prompts.py`) and asks Gemini for the thesis.

Sessions are persisted via `langgraph.checkpoint.postgres.aio.AsyncPostgresSaver` (checkpointer =
source of truth for full graph state) plus `analysis_sessions` (the query-friendly index for listing
past runs — the checkpoint tables alone can't do that query). Chart-worthy price history for the
results page is **re-fetched on demand** (`GET /api/sessions/{id}/price-history`), not persisted.

### Data sourcing

- **Stocks/ETFs**: `yfinance`, ticker format `<SYMBOL>.NS`. Universe discovered dynamically via
  `nselib.capital_market` (equity list, NIFTY 500, bhavcopy for ETF diffing) — not cached in Postgres
  (deferred; this is the same slow-ish path the old app had, just not yet fixed).
- **Mutual funds**: numeric scheme codes. Price history comes from `mf_nav_prices` (a normalized,
  row-per-day table) via a single batched query, not a live `mftool` call per scheme — this is the fix
  for the original N+1 bug. `mftool`/AMFI has no bulk or "since date" endpoint, so ingestion still
  fetches each scheme's full history individually, but only *writes* rows newer than what's already
  stored.

### Ingestion pipeline (`backend/backend/ingestion/`)

Runs daily via `.github/workflows/daily_ingest.yml` (needs a `SUPABASE_DB_URL` repo secret). Delta-sync
design: reads each scheme's `last_nav_date` up front, fetches full history per scheme (unavoidable —
no bulk source endpoint), writes only new rows in a small number of batched statements, tracks
failures in `ingestion_runs` (not just `print()`). See `backend/backend/db/README.md` for the migration
apply/verify workflow.

### Windows event loop

Two separate fixes exist for the same underlying issue (psycopg's async mode, which the LangGraph
Postgres checkpointer depends on, can't run on Windows' default ProactorEventLoop):
- `api/main.py` sets the event loop policy at import time — works for direct script/ASGI-transport
  invocation (e.g. `asyncio.run(...)`-based scripts), but **not** for the `uvicorn` CLI, which forces
  `ProactorEventLoop` internally regardless of the ambient policy.
- `api/__main__.py` (`python -m backend.api`) bypasses `uvicorn.run()`'s own loop selection entirely —
  use this for local dev on Windows. Not needed inside Docker (Linux containers don't have this issue;
  the Dockerfile uses plain `uvicorn` directly).

## Working instructions

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant
clarification.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.
