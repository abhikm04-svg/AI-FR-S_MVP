"""FastAPI app factory. Wires up the DB pool, LangGraph checkpointer, and
LLM client at startup; compiles the graph once and reuses it across
requests (plan.md Section 4).
"""
from __future__ import annotations

import asyncio
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    # psycopg's async mode (used by the LangGraph Postgres checkpointer)
    # can't run on Windows' default ProactorEventLoop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from backend.agents.graph import build_graph
from backend.api.routes import health, sessions
from backend.core.config import get_settings
from backend.db.connection import create_pool

LLM_MODEL = "gemini-2.5-flash"

# AgentState holds Pydantic models (UserPrefs, AssetRef, AssetMetrics)
# directly -- explicitly allow them through the checkpointer's msgpack
# serializer so a future LangGraph version doesn't start blocking them (see
# the "Deserializing unregistered type" deprecation warning).
_ALLOWED_MSGPACK_MODULES = [
    ("backend.data.models", "UserPrefs"),
    ("backend.data.models", "AssetRef"),
    ("backend.data.models", "AssetMetrics"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    pool = await create_pool(settings.supabase_db_url)
    app.state.background_tasks = set()

    serde = JsonPlusSerializer(allowed_msgpack_modules=_ALLOWED_MSGPACK_MODULES)
    async with AsyncPostgresSaver.from_conn_string(settings.supabase_db_url, serde=serde) as saver:
        await saver.setup()

        llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=settings.gemini_api_key)
        graph = build_graph(pool, llm).compile(checkpointer=saver)

        app.state.pool = pool
        app.state.graph = graph

        yield

    await pool.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FinAgents India API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(sessions.router, prefix="/api")
    return app


app = create_app()
