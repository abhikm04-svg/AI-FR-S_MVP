"""mf_schemes read queries used by the researcher node."""
from __future__ import annotations

import asyncpg


async def get_direct_growth_schemes(pool: asyncpg.Pool) -> dict[str, str]:
    """Returns {scheme_code: scheme_name} for all Direct+Growth schemes."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT scheme_code, scheme_name FROM mf_schemes WHERE is_direct_growth = TRUE"
        )
    return {r["scheme_code"]: r["scheme_name"] for r in rows}
