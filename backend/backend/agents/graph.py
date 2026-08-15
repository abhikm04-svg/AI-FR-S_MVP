"""LangGraph StateGraph wiring (plan.md Section 4). Linear
researcher -> analyst -> reporter -> END, with a conditional edge to an
error terminal if the analyst step finds no assets matching the risk
profile -- mirrors the current app's early-return on an empty result set.
"""
from __future__ import annotations

import asyncpg
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from backend.agents.nodes.analyst import analyst_node
from backend.agents.nodes.reporter import reporter_node
from backend.agents.nodes.researcher import researcher_node
from backend.agents.state import AgentState


def _route_after_analyst(state: AgentState) -> str:
    if state.get("status") == "error":
        return END
    return "reporter"


def build_graph(pool: asyncpg.Pool, llm: ChatGoogleGenerativeAI) -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("researcher", researcher_node(pool))
    graph.add_node("analyst", analyst_node)
    graph.add_node("reporter", reporter_node(llm))

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_conditional_edges("analyst", _route_after_analyst, {"reporter": "reporter", END: END})
    graph.add_edge("reporter", END)

    return graph
