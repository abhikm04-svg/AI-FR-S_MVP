"""Steps 2-5 of the ingestion pipeline: delta-sync NAV history per scheme.

Replaces ingest_data.py's fetch_and_save_nav()/ingest_history_parallel():
- reads every scheme's last_nav_date once, up front, instead of never
  knowing what's already stored (fetch_last_nav_dates)
- still fetches the FULL history per scheme (mftool/AMFI has no "since date"
  endpoint -- that HTTP call is unavoidable), but only WRITES entries newer
  than last_nav_date, instead of rewriting the whole blob every run
  (compute_delta)
- batches writes across ALL schemes into a small constant number of
  statements, instead of one upsert + one separate update per scheme
  (write_deltas)
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

import asyncpg
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.data.mftool_client import RobustMftool

FULL_HISTORY_DAYS = 365 * 5
DEFAULT_CONCURRENCY = 20
WRITE_CHUNK_SIZE = 5000
DATE_FORMAT = "%d-%m-%Y"


@dataclass
class SchemeSyncResult:
    scheme_code: str
    delta_rows: list[tuple[str, date, Decimal]] = field(default_factory=list)
    latest: Optional[tuple[date, Decimal]] = None
    error: Optional[str] = None


async def fetch_last_nav_dates(pool: asyncpg.Pool) -> dict[str, Optional[date]]:
    """One query, up front, so delta-sync knows in memory which dates are
    already stored per scheme before fetching or writing anything."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT scheme_code, last_nav_date FROM mf_schemes")
    return {r["scheme_code"]: r["last_nav_date"] for r in rows}


def _parse_entry(entry: dict) -> Optional[tuple[date, Decimal]]:
    try:
        entry_date = datetime.strptime(entry["date"], DATE_FORMAT).date()
        nav = Decimal(str(entry["nav"]))
    except (KeyError, ValueError, InvalidOperation, TypeError):
        return None
    return entry_date, nav


def compute_delta(
    scheme_code: str,
    raw_data: Optional[dict],
    last_nav_date: Optional[date],
) -> tuple[list[tuple[str, date, Decimal]], Optional[tuple[date, Decimal]]]:
    """Parses mftool's raw historical NAV payload into (delta_rows, latest).

    delta_rows only includes entries strictly newer than last_nav_date (or,
    for a new scheme with no last_nav_date yet, everything within the full
    FULL_HISTORY_DAYS window) -- this is the actual fix for the old
    pipeline's "rewrite the entire blob every run" behavior.

    latest is the single most recent (date, nav) point across ALL parsed
    entries (not just the delta), so mf_schemes.last_nav stays correct even
    on a day where nothing new was published.

    Malformed entries (bad date/nav) are skipped rather than aborting the
    whole scheme -- the two existing Streamlit copies already disagree on
    how strictly to parse these dates, direct evidence the source data isn't
    guaranteed uniform.
    """
    if not raw_data or "data" not in raw_data:
        return [], None

    cutoff = last_nav_date or (date.today() - timedelta(days=FULL_HISTORY_DAYS))
    delta_rows: list[tuple[str, date, Decimal]] = []
    latest: Optional[tuple[date, Decimal]] = None

    for raw_entry in raw_data["data"]:
        parsed = _parse_entry(raw_entry)
        if parsed is None:
            continue
        entry_date, nav = parsed

        if latest is None or entry_date > latest[0]:
            latest = (entry_date, nav)

        is_new = entry_date > last_nav_date if last_nav_date else entry_date >= cutoff
        if is_new:
            delta_rows.append((scheme_code, entry_date, nav))

    return delta_rows, latest


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _fetch_one_sync(mf: RobustMftool, scheme_code: str) -> dict:
    return mf.get_scheme_historical_nav(scheme_code)


async def fetch_and_compute_deltas(
    mf: RobustMftool,
    scheme_codes: list[str],
    last_nav_dates: dict[str, Optional[date]],
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[SchemeSyncResult]:
    """Fetches each scheme's raw history bounded by `concurrency` concurrent
    threads (I/O-bound calls to AMFI; validate empirically before raising
    much past the default -- no documented rate limit, but also no
    guarantee), retrying transient failures via tenacity so they don't count
    as permanent misses. Explicitly sized ThreadPoolExecutor, since
    asyncio.to_thread's default executor caps around min(32, cpu_count+4)
    regardless of the semaphore limit.
    """
    executor = ThreadPoolExecutor(max_workers=concurrency)
    loop = asyncio.get_running_loop()
    semaphore = asyncio.Semaphore(concurrency)
    results: list[SchemeSyncResult] = []

    async def process(code: str) -> None:
        async with semaphore:
            try:
                raw = await loop.run_in_executor(executor, _fetch_one_sync, mf, code)
            except Exception as exc:  # one bad scheme must not sink the run
                results.append(SchemeSyncResult(scheme_code=code, error=str(exc)))
                return
            delta_rows, latest = compute_delta(code, raw, last_nav_dates.get(code))
            results.append(
                SchemeSyncResult(scheme_code=code, delta_rows=delta_rows, latest=latest)
            )

    try:
        await asyncio.gather(*(process(c) for c in scheme_codes))
    finally:
        executor.shutdown(wait=False)

    return results


async def write_deltas(pool: asyncpg.Pool, results: list[SchemeSyncResult]) -> None:
    """Batched write phase: one chunked INSERT into mf_nav_prices across all
    schemes' delta rows (idempotent -- ON CONFLICT DO NOTHING, safe since
    published NAVs are immutable), plus a single multi-row UPDATE into
    mf_schemes via unnest() -- replacing both the double-write and the
    per-scheme write count from the old pipeline with a small constant
    number of batched round trips.
    """
    all_rows = [row for r in results for row in r.delta_rows]

    async with pool.acquire() as conn:
        for i in range(0, len(all_rows), WRITE_CHUNK_SIZE):
            chunk = all_rows[i : i + WRITE_CHUNK_SIZE]
            await conn.executemany(
                """
                INSERT INTO mf_nav_prices (scheme_code, nav_date, nav)
                VALUES ($1, $2, $3)
                ON CONFLICT (scheme_code, nav_date) DO NOTHING
                """,
                chunk,
            )

        synced = [(r.scheme_code, r.latest[0], r.latest[1]) for r in results if r.latest]
        if synced:
            await conn.execute(
                """
                UPDATE mf_schemes s
                SET last_nav_date = v.nav_date,
                    last_nav = v.nav,
                    last_synced_at = now()
                FROM (
                    SELECT unnest($1::text[]) AS scheme_code,
                           unnest($2::date[]) AS nav_date,
                           unnest($3::numeric[]) AS nav
                ) v
                WHERE s.scheme_code = v.scheme_code
                """,
                [s[0] for s in synced],
                [s[1] for s in synced],
                [s[2] for s in synced],
            )
