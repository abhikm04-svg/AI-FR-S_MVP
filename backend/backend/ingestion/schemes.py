"""Step 1 of the ingestion pipeline: sync the mf_schemes catalog from AMFI.

Reasonably efficient already in the old ingest_data.py (plan.md Section 3,
item 1) -- logic is unchanged, just moved into the new package and switched
to the defensive RobustMftool parser (the old ingest_data.py used plain
Mftool, missing that fix).
"""
from __future__ import annotations

import asyncio

import asyncpg

from backend.data.mftool_client import RobustMftool

CHUNK_SIZE = 500


def filter_direct_growth(all_codes: dict[str, str]) -> list[tuple[str, str]]:
    """Keep only 'Direct' + 'Growth' plan schemes, matching the filtering
    rule used throughout the app (Application/app.py, ingest_data.py)."""
    return [
        (code, name)
        for code, name in all_codes.items()
        if "Direct" in name and "Growth" in name
    ]


async def sync_schemes(pool: asyncpg.Pool, mf: RobustMftool) -> int:
    """Fetch AMFI scheme codes, filter to Direct+Growth, batch-upsert into
    mf_schemes. Returns the number of schemes upserted."""
    all_codes = await asyncio.to_thread(mf.get_scheme_codes)
    filtered = filter_direct_growth(all_codes)

    async with pool.acquire() as conn:
        for i in range(0, len(filtered), CHUNK_SIZE):
            chunk = filtered[i : i + CHUNK_SIZE]
            await conn.executemany(
                """
                INSERT INTO mf_schemes (scheme_code, scheme_name, is_direct_growth)
                VALUES ($1, $2, TRUE)
                ON CONFLICT (scheme_code) DO UPDATE
                    SET scheme_name = EXCLUDED.scheme_name,
                        is_direct_growth = TRUE
                """,
                chunk,
            )
    return len(filtered)
