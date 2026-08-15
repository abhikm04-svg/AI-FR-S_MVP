"""
Applies the SQL files in migrations/ against a Postgres database, in filename
order, skipping any already recorded in schema_migrations. Each migration runs
in its own transaction.

Standalone by design (no dependency on the rest of the backend package, which
doesn't exist yet as of Phase 1) -- just this script plus asyncpg.

Usage:
    pip install asyncpg
    python apply_migrations.py --dsn "postgresql://..."
    # or:
    SUPABASE_DB_URL="postgresql://..." python apply_migrations.py

    python apply_migrations.py --dry-run   # list what would run, without connecting
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

CREATE_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def pending_migrations(already_applied: set[str]) -> list[Path]:
    all_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return [f for f in all_files if f.name not in already_applied]


async def run(dsn: str, dry_run: bool) -> None:
    import asyncpg

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(CREATE_TRACKING_TABLE)
        rows = await conn.fetch("SELECT filename FROM schema_migrations")
        already_applied = {r["filename"] for r in rows}

        to_run = pending_migrations(already_applied)
        if not to_run:
            print("Nothing to apply -- all migrations already recorded.")
            return

        for path in to_run:
            print(f"Applying {path.name}...")
            sql = path.read_text(encoding="utf-8")
            if dry_run:
                continue
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)", path.name
                )
            print(f"  done.")

        if dry_run:
            print("(dry run -- nothing was executed)")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.getenv("SUPABASE_DB_URL"),
        help="Postgres connection string. Defaults to $SUPABASE_DB_URL. "
        "This must be the direct Postgres DSN from Supabase's dashboard "
        "(Project Settings -> Database -> Connection string), NOT the "
        "SUPABASE_URL/anon-key REST API pair used elsewhere in this repo.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List pending migration files without connecting or executing anything.",
    )
    args = parser.parse_args()

    if args.dry_run and not args.dsn:
        already_applied: set[str] = set()
        to_run = pending_migrations(already_applied)
        print("Pending migrations (dry run, no DB connection):")
        for path in to_run:
            print(f"  {path.name}")
        return

    if not args.dsn:
        print(
            "No DSN provided. Pass --dsn or set SUPABASE_DB_URL.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(run(args.dsn, args.dry_run))


if __name__ == "__main__":
    main()
