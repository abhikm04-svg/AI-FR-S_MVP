"""FastAPI dependency providers."""
from __future__ import annotations

import asyncpg
from fastapi import Header, HTTPException, Request
from langgraph.graph.state import CompiledStateGraph


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_graph(request: Request) -> CompiledStateGraph:
    return request.app.state.graph


def get_user_id(x_user_id: str = Header(...)) -> str:
    """Anonymous per-browser UUID, generated client-side and sent as a
    header on every request (no login screen for v1, per plan.md)."""
    if not x_user_id:
        raise HTTPException(status_code=400, detail="X-User-Id header is required")
    return x_user_id
