"""Shared data shapes for the researcher/analyst/reporter pipeline. Replaces
the ad hoc dicts/DataFrame rows used across the two Streamlit copies.
"""
from __future__ import annotations

from typing import Optional, Union

from pydantic import BaseModel


class AssetRef(BaseModel):
    """A candidate instrument before any metrics have been computed."""

    ticker: str
    name: str
    instrument_type: str


class AssetMetrics(BaseModel):
    """Technical + fundamental metrics for one instrument, post-analysis."""

    ticker: str
    name: str
    last_price_inr: float
    return_1y_pct: float
    volatility_pct: float
    sharpe_ratio: float
    trend: str
    # Default covers sessions checkpointed before this field existed (no DB
    # migration involved -- analyzed_metrics lives only in the LangGraph
    # checkpoint blob).
    instrument_type: str = "Other"

    market_cap_cr: str = "N/A"
    pe_ratio: str = "N/A"
    pb_ratio: str = "N/A"
    debt_to_equity: str = "N/A"
    roe: str = "N/A"
    eps_ttm: str = "N/A"
    dividend_yield: str = "N/A"
    expense_ratio: str = "N/A"


class UserPrefs(BaseModel):
    """Mirrors the sidebar/profile-form inputs from the Streamlit apps."""

    instruments: list[str]
    risk: Union[str, tuple[str, str]]
    target_return: str
    horizon: str
    goal: str
    capital: Optional[float] = None
