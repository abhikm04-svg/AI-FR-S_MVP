from backend.agents.prompts import build_report_prompt
from backend.data.models import AssetMetrics, UserPrefs


def _metric(ticker: str, sharpe: float) -> AssetMetrics:
    return AssetMetrics(
        ticker=ticker,
        name=f"{ticker} Fund",
        last_price_inr=100.0,
        return_1y_pct=12.0,
        volatility_pct=15.0,
        sharpe_ratio=sharpe,
        trend="Bullish",
    )


def _prefs() -> UserPrefs:
    return UserPrefs(
        instruments=["Stocks"],
        risk="Moderate",
        target_return="12",
        horizon="Long Term (5+ yrs)",
        goal="Wealth Creation",
    )


def test_prompt_includes_top_5_in_json_context_but_no_ranked_picks_section():
    # The UI renders its own deterministic per-category "Top Recommendations"
    # grid from the quantitative data -- the prompt must not also ask the LLM
    # for a ranked picks list, which could disagree with it.
    metrics = [_metric(t, s) for t, s in [("A", 2.0), ("B", 1.5), ("C", 1.0), ("D", 0.5), ("E", 0.2), ("F", 0.1)]]
    prompt = build_report_prompt(metrics, _prefs())
    assert '"A Fund"' in prompt  # top 5 present in the raw JSON grounding block
    assert '"E Fund"' in prompt
    assert '"F Fund"' not in prompt  # 6th asset excluded, only top 5 passed
    assert "Top 3 Recommendations" not in prompt
    assert "# **Top" not in prompt  # no ranked-picks heading of any kind


def test_prompt_handles_fewer_than_three_picks():
    metrics = [_metric("A", 2.0)]
    prompt = build_report_prompt(metrics, _prefs())
    assert '"A Fund"' in prompt


def test_prompt_includes_user_profile_fields():
    prompt = build_report_prompt([_metric("A", 1.0)], _prefs())
    assert "Moderate Investor" in prompt
    assert "Wealth Creation" in prompt
