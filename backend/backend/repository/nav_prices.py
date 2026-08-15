"""The batched NAV read that replaces the app's old N+1 query loop
(plan.md Section 2, and the original bug in Application/app.py's
fetch_market_data). One round trip for the entire scheme universe instead
of one per scheme code.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable, Mapping

import asyncpg


def _group_rows(
    scheme_codes: list[str], rows: Iterable[Mapping]
) -> dict[str, list[tuple[date, Decimal]]]:
    result: dict[str, list[tuple[date, Decimal]]] = {code: [] for code in scheme_codes}
    for row in rows:
        result[row["scheme_code"]].append((row["nav_date"], row["nav"]))
    return result


async def get_nav_prices_batch(
    pool: asyncpg.Pool, scheme_codes: list[str], since: date
) -> dict[str, list[tuple[date, Decimal]]]:
    """Returns {scheme_code: [(nav_date, nav), ...]} sorted by date ascending,
    for every code in scheme_codes with nav_date >= since. Single round trip
    regardless of how many codes are requested.
    """
    if not scheme_codes:
        return {}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT scheme_code, nav_date, nav
            FROM mf_nav_prices
            WHERE scheme_code = ANY($1::text[]) AND nav_date >= $2
            ORDER BY scheme_code, nav_date
            """,
            scheme_codes,
            since,
        )

    return _group_rows(scheme_codes, rows)
