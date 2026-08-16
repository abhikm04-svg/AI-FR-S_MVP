"""Researcher node: ports MarketResearcher.execute(). Asset universe
discovery + raw price fetch, reduced immediately to technical metrics so raw
OHLC/NAV series never enter the checkpointed graph state (plan.md Section 4).
No LLM -- deterministic data + math, same as the current app.
"""
from __future__ import annotations

from typing import Awaitable, Callable

import asyncpg

from backend.agents.state import AgentState
from backend.data import market_data
from backend.repository.schemes import get_direct_growth_schemes


def researcher_node(pool: asyncpg.Pool) -> Callable[[AgentState], Awaitable[dict]]:
    async def _run(state: AgentState) -> dict:
        user_prefs = state["user_prefs"]

        mf_schemes = await get_direct_growth_schemes(pool)
        asset_universe = await market_data.get_asset_universe(user_prefs.instruments, mf_schemes)

        tickers = [a.ticker for a in asset_universe]
        price_series = await market_data.fetch_market_data(pool, tickers)

        scanned = []
        for asset in asset_universe:
            close = price_series.get(asset.ticker)
            if close is None:
                continue
            metrics = market_data.compute_technical_metrics(
                asset.ticker, asset.name, asset.instrument_type, close
            )
            if metrics:
                scanned.append(metrics)

        return {
            "asset_universe": asset_universe,
            "analyzed_metrics": scanned,
            "status": "analyzing",
        }

    return _run
