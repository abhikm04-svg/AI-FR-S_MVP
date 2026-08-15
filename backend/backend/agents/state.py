"""LangGraph shared state. Deliberately excludes raw OHLC/NAV series/
DataFrames -- those are fetched and reduced to AssetMetrics immediately
inside the researcher node and never returned from it, since
AsyncPostgresSaver blobs the entire state at every checkpoint (plan.md
Section 4).
"""
from __future__ import annotations

from typing import Optional, TypedDict

from backend.data.models import AssetMetrics, AssetRef, UserPrefs


class AgentState(TypedDict):
    user_prefs: UserPrefs
    asset_universe: list[AssetRef]
    analyzed_metrics: list[AssetMetrics]
    final_thesis: str
    status: str
    error: Optional[str]
