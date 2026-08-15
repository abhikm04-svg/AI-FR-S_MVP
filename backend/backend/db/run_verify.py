"""
Runs verify_backfill.sql against a Postgres database and prints any
mismatched rows. Companion to apply_migrations.py -- same standalone,
asyncpg-only design.

Usage:
    python run_verify.py --dsn "postgresql://..."
    # or: SUPABASE_DB_URL="postgresql://..." python run_verify.py
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

VERIFY_SQL = Path(__file__).parent / "verify_backfill.sql"


async def run(dsn: str) -> None:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(VERIFY_SQL.read_text(encoding="utf-8"))
        if not rows:
            print("OK: 0 mismatched schemes -- backfill counts match mf_nav_history.")
            return
        print(f"MISMATCH: {len(rows)} scheme(s) differ (showing up to 50):")
        print(f"{'scheme_code':<15}{'blob_count':>12}{'normalized_count':>18}")
        for r in rows:
            print(f"{r['scheme_code']:<15}{r['blob_count']:>12}{r['normalized_count']:>18}")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default=os.getenv("SUPABASE_DB_URL"))
    args = parser.parse_args()
    if not args.dsn:
        print("No DSN provided. Pass --dsn or set SUPABASE_DB_URL.", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run(args.dsn))


if __name__ == "__main__":
    main()
