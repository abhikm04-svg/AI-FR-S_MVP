from backend.agents.nodes.analyst import TOP_N, filter_and_rank, risk_bounds
from backend.data.models import AssetMetrics


def _metric(ticker: str, volatility: float, sharpe: float) -> AssetMetrics:
    return AssetMetrics(
        ticker=ticker,
        name=ticker,
        last_price_inr=100.0,
        return_1y_pct=10.0,
        volatility_pct=volatility,
        sharpe_ratio=sharpe,
        trend="Bullish",
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
    metrics = [_metric(str(i), volatility=15, sharpe=float(i)) for i in range(TOP_N + 10)]
    result = filter_and_rank(metrics, "Moderate")
    assert len(result) == TOP_N
    assert result[0].ticker == str(TOP_N + 9)  # highest sharpe first


def test_filter_and_rank_empty_when_nothing_matches():
    assert filter_and_rank([_metric("A", volatility=50, sharpe=1.0)], "Moderate") == []
