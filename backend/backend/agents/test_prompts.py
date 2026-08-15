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


def test_prompt_includes_top_3_picks_in_order():
    metrics = [_metric("A", 2.0), _metric("B", 1.5), _metric("C", 1.0), _metric("D", 0.5)]
    prompt = build_report_prompt(metrics, _prefs())
    assert "**A Fund**" in prompt
    assert "**B Fund**" in prompt
    assert "**C Fund**" in prompt
    assert "**D Fund**" not in prompt  # only top 3 get a ranked bullet; D still appears in the raw JSON context


def test_prompt_handles_fewer_than_three_picks():
    metrics = [_metric("A", 2.0)]
    prompt = build_report_prompt(metrics, _prefs())
    assert "**A Fund**" in prompt
    assert "**Asset 2**" in prompt
    assert "**Asset 3**" in prompt


def test_prompt_includes_user_profile_fields():
    prompt = build_report_prompt([_metric("A", 1.0)], _prefs())
    assert "Moderate Investor" in prompt
    assert "Wealth Creation" in prompt
