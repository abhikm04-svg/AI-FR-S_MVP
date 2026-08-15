"""analysis_sessions CRUD -- the query-friendly index alongside the
LangGraph checkpointer (plan.md Section 2). The checkpointer remains the
source of truth for full graph state; this table is what makes "list my
past runs", status tracking, and reconstructing a session's UserPrefs to
(re)trigger a run possible.
"""
from __future__ import annotations

import uuid
from typing import Optional

import asyncpg

from backend.data.models import UserPrefs


async def create_session(pool: asyncpg.Pool, user_id: str, user_prefs: UserPrefs) -> dict:
    thread_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO analysis_sessions (thread_id, user_id, goal, user_prefs)
            VALUES ($1, $2, $3, $4::jsonb)
            RETURNING id, thread_id, status, created_at
            """,
            thread_id,
            user_id,
            user_prefs.goal,
            user_prefs.model_dump_json(),
        )
    return dict(row)


async def get_session(pool: asyncpg.Pool, session_id: uuid.UUID) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM analysis_sessions WHERE id = $1", session_id)
    return dict(row) if row else None


async def list_sessions(pool: asyncpg.Pool, user_id: str) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, thread_id, goal, status, created_at "
            "FROM analysis_sessions WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
    return [dict(r) for r in rows]


async def update_status(
    pool: asyncpg.Pool,
    session_id: uuid.UUID,
    status: str,
    error_message: Optional[str] = None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE analysis_sessions
            SET status = $2, error_message = $3, updated_at = now()
            WHERE id = $1
            """,
            session_id,
            status,
            error_message,
        )
