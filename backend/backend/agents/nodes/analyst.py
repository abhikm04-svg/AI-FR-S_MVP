"""Analyst node: ports FinancialAnalyst.execute(). Risk-slab filtering,
Sharpe-ratio ranking (technical metrics were already computed by the
researcher node -- this just ranks/filters them), fundamentals fetch scoped
to the top-N shortlist only (already the right design in the current app --
kept as-is). No LLM.
"""
from __future__ import annotations

from typing import Union

from backend.agents.state import AgentState
from backend.data.market_data import fetch_fundamentals
from backend.data.models import AssetMetrics

# Volatility slabs (annualized SD), adjusted for Indian equity markets
# (Nifty ~12-15%, individual stocks ~20-40%). Ported from
# FinancialAnalyst.execute()'s risk_slabs dict.
RISK_SLABS: dict[str, tuple[float, float]] = {
    "Ultra Conservative": (0, 5),
    "Conservative": (5, 10),
    "Moderate": (10, 20),
    "Aggressive": (20, 30),
    "Very Aggressive": (30, 40),
    "Speculative / High Alpha": (40, 1000),
}

TOP_N = 20


def risk_bounds(risk: Union[str, tuple[str, str]]) -> tuple[float, float]:
    """risk is either a single slab name, or a (start, end) tuple for a
    range selection -- mirrors the Streamlit apps' Allow Range Selection
    toggle."""
    if isinstance(risk, (tuple, list)):
        start, end = risk
        return RISK_SLABS[start][0], RISK_SLABS[end][1]
    return RISK_SLABS.get(risk, (0, 100))


def filter_and_rank(
    metrics: list[AssetMetrics], risk: Union[str, tuple[str, str]]
) -> list[AssetMetrics]:
    min_vol, max_vol = risk_bounds(risk)
    filtered = [m for m in metrics if min_vol <= m.volatility_pct <= max_vol]
    filtered.sort(key=lambda m: m.sharpe_ratio, reverse=True)
    return filtered[:TOP_N]


async def analyst_node(state: AgentState) -> dict:
    scanned = state["analyzed_metrics"]
    user_prefs = state["user_prefs"]

    top_picks = filter_and_rank(scanned, user_prefs.risk)
    if not top_picks:
        return {
            "analyzed_metrics": [],
            "status": "error",
            "error": "No assets matched the selected risk profile.",
        }

    enriched: list[AssetMetrics] = []
    for m in top_picks:
        funds = await fetch_fundamentals(m.ticker)
        enriched.append(m.model_copy(update=funds))

    return {"analyzed_metrics": enriched, "status": "reporting"}
