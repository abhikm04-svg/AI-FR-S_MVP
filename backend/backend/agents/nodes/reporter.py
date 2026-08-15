"""Reporter node: the one real LLM node in the pipeline -- ports
BusinessAnalyst.execute(). Researcher/analyst stay deterministic plain
functions; wrapping them in an LLM-driven agent loop would be slower, less
deterministic, and harder to test than what the current app already does
(plan.md Section 0 pushback #2).
"""
from __future__ import annotations

from typing import Awaitable, Callable

from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.prompts import build_report_prompt
from backend.agents.state import AgentState


def reporter_node(llm: ChatGoogleGenerativeAI) -> Callable[[AgentState], Awaitable[dict]]:
    async def _run(state: AgentState) -> dict:
        metrics = state["analyzed_metrics"]
        user_prefs = state["user_prefs"]

        if not metrics:
            return {
                "final_thesis": "No suitable assets found based on the analysis.",
                "status": "done",
            }

        prompt = build_report_prompt(metrics, user_prefs)
        response = await llm.ainvoke(prompt)
        return {"final_thesis": response.content, "status": "done"}

    return _run
