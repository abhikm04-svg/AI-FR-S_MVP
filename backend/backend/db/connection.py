"""asyncpg connection pool factory -- the direct Postgres connection used by
the ingestion pipeline, repositories (Phase 3), and the LangGraph checkpointer
(Phase 3). Distinct from the Supabase REST URL/anon-key pair used by the
Streamlit apps.
"""
from __future__ import annotations

import asyncpg


async def create_pool(dsn: str, min_size: int = 1, max_size: int = 10) -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn, min_size=min_size, max_size=max_size)
