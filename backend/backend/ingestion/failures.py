"""ingestion_runs bookkeeping -- replaces ingest_data.py's print()-only
failure handling, which is invisible outside a GitHub Actions log tail.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import asyncpg


async def start_run(pool: asyncpg.Pool, total_schemes: Optional[int] = None) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO ingestion_runs (started_at, status, total_schemes)
            VALUES (now(), 'running', $1)
            RETURNING id
            """,
            total_schemes,
        )
    return row["id"]


def build_failed_codes(errors: list[tuple[str, str]]) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [{"code": code, "error": error, "at": now} for code, error in errors]


async def finish_run(
    pool: asyncpg.Pool,
    run_id: int,
    succeeded: int,
    failed: int,
    failed_codes: list[dict],
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE ingestion_runs
            SET finished_at = now(),
                status = 'completed',
                succeeded = $2,
                failed = $3,
                failed_codes = $4::jsonb
            WHERE id = $1
            """,
            run_id,
            succeeded,
            failed,
            json.dumps(failed_codes),
        )


async def fail_run(pool: asyncpg.Pool, run_id: int, error_message: str) -> None:
    """The run itself crashed (e.g. lost DB connection), as opposed to
    individual scheme fetch failures, which go through finish_run's
    failed_codes instead."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE ingestion_runs
            SET finished_at = now(),
                status = 'failed',
                failed_codes = failed_codes || $2::jsonb
            WHERE id = $1
            """,
            run_id,
            json.dumps([{"error": error_message}]),
        )
