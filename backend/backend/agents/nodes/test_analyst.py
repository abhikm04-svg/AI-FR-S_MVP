from unittest.mock import AsyncMock, patch

from backend.agents.nodes import analyst as analyst_module
from backend.agents.nodes.analyst import TOP_N_PER_CATEGORY, analyst_node, filter_and_rank, risk_bounds
from backend.data.models import AssetMetrics, UserPrefs


def _metric(
    ticker: str, volatility: float, sharpe: float, instrument_type: str = "Stocks"
) -> AssetMetrics:
    return AssetMetrics(
        ticker=ticker,
        name=ticker,
        last_price_inr=100.0,
        return_1y_pct=10.0,
        volatility_pct=volatility,
        sharpe_ratio=sharpe,
        trend="Bullish",
        instrument_type=instrument_type,
    )


def test_risk_bounds_single_slab():
    assert risk_bounds("Moderate") == (10, 20)


def test_risk_bounds_unknown_slab_defaults_wide_open():
    assert risk_bounds("Not A Slab") == (0, 100)


def test_risk_bounds_range_spans_min_of_start_to_max_of_end():
    assert risk_bounds(("Conservative", "Moderate")) == (5, 20)


def test_filter_and_rank_excludes_out_of_band_volatility():
    metrics = [_metric("A", volatility=3, sharpe=1.0), _metric("B", volatility=15, sharpe=0.5)]
    result = filter_and_rank(metrics, "Moderate")
    assert [m.ticker for m in result] == ["B"]


def test_filter_and_rank_sorts_by_sharpe_descending():
    metrics = [
        _metric("LOW", volatility=15, sharpe=0.5),
        _metric("HIGH", volatility=15, sharpe=2.0),
    ]
    result = filter_and_rank(metrics, "Moderate")
    assert [m.ticker for m in result] == ["HIGH", "LOW"]


def test_filter_and_rank_caps_at_top_n():
    n = TOP_N_PER_CATEGORY
    metrics = [_metric(str(i), volatility=15, sharpe=float(i)) for i in range(n + 10)]
    result = filter_and_rank(metrics, "Moderate")
    assert len(result) == n
    assert result[0].ticker == str(n + 9)  # highest sharpe first


def test_filter_and_rank_empty_when_nothing_matches():
    assert filter_and_rank([_metric("A", volatility=50, sharpe=1.0)], "Moderate") == []


def _user_prefs(risk="Moderate") -> UserPrefs:
    return UserPrefs(
        instruments=["Stocks", "Gold/Commodities"],
        risk=risk,
        target_return="12",
        horizon="Long Term (5+ yrs)",
        goal="Wealth Creation",
    )


async def test_analyst_node_keeps_small_category_alongside_large_one():
    # A 2-asset gold category alongside a 50-asset stock category -- a flat
    # global top-N-by-Sharpe would have dropped gold entirely since stocks
    # here all rank higher. Per-category ranking must keep both golds.
    stocks = [_metric(f"S{i}", volatility=15, sharpe=5.0 + i, instrument_type="Stocks") for i in range(50)]
    golds = [
        _metric("GOLD1", volatility=12, sharpe=0.5, instrument_type="Gold/Commodities"),
        _metric("GOLD2", volatility=12, sharpe=0.3, instrument_type="Gold/Commodities"),
    ]
    state = {
        "analyzed_metrics": stocks + golds,
        "user_prefs": _user_prefs(),
    }

    with patch.object(analyst_module, "fetch_fundamentals", AsyncMock(return_value={})):
        result = await analyst_node(state)

    tickers = {m.ticker for m in result["analyzed_metrics"]}
    assert "GOLD1" in tickers
    assert "GOLD2" in tickers
    assert result["status"] == "reporting"


async def test_analyst_node_errors_when_no_category_matches_risk():
    state = {
        "analyzed_metrics": [_metric("A", volatility=50, sharpe=1.0)],
        "user_prefs": _user_prefs(),
    }

    result = await analyst_node(state)

    assert result["analyzed_metrics"] == []
    assert result["status"] == "error"
