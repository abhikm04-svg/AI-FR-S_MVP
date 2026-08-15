"""Session endpoints: create, trigger a run, stream progress, fetch
results, and list history (plan.md Section 4).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Optional, Union

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.agents.state import AgentState
from backend.api.deps import get_graph, get_pool, get_user_id
from backend.data.models import UserPrefs
from backend.repository import sessions as sessions_repo

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    instruments: list[str]
    risk: Union[str, tuple[str, str]]
    target_return: str
    horizon: str
    goal: str
    capital: Optional[float] = None


class SessionSummary(BaseModel):
    id: uuid.UUID
    thread_id: str
    status: str


@router.post("", response_model=SessionSummary)
async def create_session(
    body: CreateSessionRequest,
    pool: asyncpg.Pool = Depends(get_pool),
    user_id: str = Depends(get_user_id),
) -> SessionSummary:
    user_prefs = UserPrefs(**body.model_dump())
    row = await sessions_repo.create_session(pool, user_id, user_prefs)
    return SessionSummary(id=row["id"], thread_id=row["thread_id"], status=row["status"])


async def _run_graph(
    graph: CompiledStateGraph,
    pool: asyncpg.Pool,
    session_id: uuid.UUID,
    thread_id: str,
    user_prefs: UserPrefs,
) -> None:
    config = {"configurable": {"thread_id": thread_id}}
    try:
        await sessions_repo.update_status(pool, session_id, "running")
        initial_state: AgentState = {
            "user_prefs": user_prefs,
            "asset_universe": [],
            "analyzed_metrics": [],
            "final_thesis": "",
            "status": "researching",
            "error": None,
        }
        async for _ in graph.astream(initial_state, config=config, stream_mode="updates"):
            pass

        final_state = await graph.aget_state(config)
        if final_state.values.get("status") == "error":
            await sessions_repo.update_status(
                pool, session_id, "failed", final_state.values.get("error")
            )
        else:
            await sessions_repo.update_status(pool, session_id, "completed")
    except Exception as exc:  # a crashed run must still be reflected in status
        await sessions_repo.update_status(pool, session_id, "failed", str(exc))


@router.post("/{session_id}/run", status_code=202)
async def start_run(
    session_id: uuid.UUID,
    request: Request,
    pool: asyncpg.Pool = Depends(get_pool),
    graph: CompiledStateGraph = Depends(get_graph),
) -> dict:
    row = await sessions_repo.get_session(pool, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_prefs = UserPrefs.model_validate_json(row["user_prefs"])

    # Detached task, not awaited here -- this is what makes "close the
    # browser, come back later" work. Keep a strong reference on app.state
    # so it isn't garbage-collected mid-run (a real asyncio gotcha for
    # fire-and-forget tasks).
    task = asyncio.create_task(_run_graph(graph, pool, session_id, row["thread_id"], user_prefs))
    request.app.state.background_tasks.add(task)
    task.add_done_callback(request.app.state.background_tasks.discard)

    return {"status": "started"}


@router.get("/{session_id}")
async def get_session_detail(
    session_id: uuid.UUID,
    pool: asyncpg.Pool = Depends(get_pool),
    graph: CompiledStateGraph = Depends(get_graph),
) -> dict:
    row = await sessions_repo.get_session(pool, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result: dict = {
        "id": str(row["id"]),
        "thread_id": row["thread_id"],
        "goal": row["goal"],
        "status": row["status"],
        "error_message": row["error_message"],
        "created_at": row["created_at"].isoformat(),
    }

    if row["status"] in ("running", "completed", "failed"):
        config = {"configurable": {"thread_id": row["thread_id"]}}
        state = await graph.aget_state(config)
        if state.values:
            metrics = state.values.get("analyzed_metrics", [])
            result["analyzed_metrics"] = [
                m.model_dump() if hasattr(m, "model_dump") else m for m in metrics
            ]
            result["final_thesis"] = state.values.get("final_thesis", "")

    return result


@router.get("")
async def list_sessions(
    pool: asyncpg.Pool = Depends(get_pool), user_id: str = Depends(get_user_id)
) -> list[dict]:
    rows = await sessions_repo.list_sessions(pool, user_id)
    return [
        {
            "id": str(r["id"]),
            "thread_id": r["thread_id"],
            "goal": r["goal"],
            "status": r["status"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]


@router.get("/{session_id}/stream")
async def stream_session(
    session_id: uuid.UUID, pool: asyncpg.Pool = Depends(get_pool)
) -> EventSourceResponse:
    async def _events():
        last_status = None
        while True:
            row = await sessions_repo.get_session(pool, session_id)
            if row is None:
                yield {"event": "error", "data": "session not found"}
                return
            status = row["status"]
            if status != last_status:
                yield {"event": "status", "data": json.dumps({"status": status})}
                last_status = status
            if status in ("completed", "failed"):
                return
            await asyncio.sleep(1.0)

    return EventSourceResponse(_events())
