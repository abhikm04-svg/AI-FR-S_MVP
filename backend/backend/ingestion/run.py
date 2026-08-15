"""CLI entrypoint for the ingestion pipeline.

Once the parallel-run/diff validation period (plan.md Phase 2) is complete,
.github/workflows/daily_ingest.yml's run step switches from
`python ingest_data.py` to:
    python -m backend.ingestion.run

Local usage (run from the outer backend/ directory):
    SUPABASE_DB_URL=... python -m backend.ingestion.run
    python -m backend.ingestion.run --dsn "postgresql://..." --limit 20
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv

from backend.data.mftool_client import RobustMftool
from backend.db.connection import create_pool
from backend.ingestion.failures import build_failed_codes, fail_run, finish_run, start_run
from backend.ingestion.nav_history import (
    DEFAULT_CONCURRENCY,
    fetch_and_compute_deltas,
    fetch_last_nav_dates,
    write_deltas,
)
from backend.ingestion.schemes import sync_schemes


async def run(dsn: str, limit: Optional[int], concurrency: int) -> None:
    pool = await create_pool(dsn)
    mf = RobustMftool()
    run_id = None
    try:
        print("Syncing scheme catalog...")
        scheme_count = await sync_schemes(pool, mf)
        print(f"  {scheme_count} Direct+Growth schemes in mf_schemes.")

        last_nav_dates = await fetch_last_nav_dates(pool)
        scheme_codes = list(last_nav_dates.keys())
        if limit:
            scheme_codes = scheme_codes[:limit]

        run_id = await start_run(pool, total_schemes=len(scheme_codes))
        print(
            f"Ingestion run #{run_id} started -- {len(scheme_codes)} schemes, "
            f"concurrency={concurrency}."
        )

        t0 = time.perf_counter()
        results = await fetch_and_compute_deltas(
            mf, scheme_codes, last_nav_dates, concurrency=concurrency
        )
        elapsed = time.perf_counter() - t0

        errors = [(r.scheme_code, r.error) for r in results if r.error]
        succeeded = len(results) - len(errors)
        total_new_rows = sum(len(r.delta_rows) for r in results)

        await write_deltas(pool, results)
        await finish_run(
            pool,
            run_id,
            succeeded=succeeded,
            failed=len(errors),
            failed_codes=build_failed_codes(errors),
        )

        print(
            f"Done in {elapsed:.1f}s -- {succeeded} succeeded, {len(errors)} failed, "
            f"{total_new_rows} new NAV rows written."
        )
        if errors:
            shown = ", ".join(code for code, _ in errors[:10])
            more = " ..." if len(errors) > 10 else ""
            print(f"Failed schemes (see ingestion_runs #{run_id} for details): {shown}{more}")
    except Exception as exc:
        if run_id is not None:
            await fail_run(pool, run_id, str(exc))
        raise
    finally:
        await pool.close()


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default=os.getenv("SUPABASE_DB_URL"))
    parser.add_argument(
        "--limit", type=int, default=None, help="Only sync the first N schemes (for testing)."
    )
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    args = parser.parse_args()

    if not args.dsn:
        print("No DSN provided. Pass --dsn or set SUPABASE_DB_URL.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(run(args.dsn, args.limit, args.concurrency))


if __name__ == "__main__":
    main()
