"""Dev/local server entrypoint: `python -m backend.api` from the outer
backend/ directory.

uvicorn's own `Server.run()` forces `asyncio.ProactorEventLoop` on Windows
(uvicorn/loops/asyncio.py) regardless of any ambient event loop policy --
incompatible with psycopg's async mode, which the LangGraph Postgres
checkpointer depends on. Bypassing `Server.run()` and driving `server.serve()`
through `asyncio.run(..., loop_factory=...)` directly is the only way to
actually get a SelectorEventLoop on Windows.
"""
from __future__ import annotations

import asyncio
import sys

import uvicorn


async def _serve() -> None:
    config = uvicorn.Config("backend.api.main:app", host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(_serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(_serve())
