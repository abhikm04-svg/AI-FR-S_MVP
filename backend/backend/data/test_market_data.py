from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd

from backend.data.market_data import (
    _series_from_nav_rows,
    _series_from_yf,
    _shape_fundamentals,
    compute_technical_metrics,
)


def test_series_from_nav_rows_sorts_and_converts_to_float():
    rows = [
        (date(2024, 1, 2), Decimal("11.0")),
        (date(2024, 1, 1), Decimal("10.0")),
    ]
    series = _series_from_nav_rows(rows)
    assert list(series.values) == [10.0, 11.0]
    assert series.index[0] < series.index[1]


def test_series_from_nav_rows_empty():
    assert _series_from_nav_rows([]).empty


def test_series_from_yf_single_ticker_columns():
    df = pd.DataFrame({"Close": [1.0, 2.0], "Open": [1.0, 2.0]})
    result = _series_from_yf(df, "ANY.NS")
    assert list(result.values) == [1.0, 2.0]


def test_series_from_yf_missing_ticker_in_multiindex_returns_none():
    cols = pd.MultiIndex.from_product([["AAA.NS"], ["Close", "Open"]])
    df = pd.DataFrame([[1.0, 1.0]], columns=cols)
    assert _series_from_yf(df, "ZZZ.NS") is None


def test_series_from_yf_empty_dataframe_returns_none():
    assert _series_from_yf(pd.DataFrame(), "ANY.NS") is None


def _rising_series(n: int, start: float = 100.0, step: float = 0.5) -> pd.Series:
    idx = pd.date_range("2023-01-01", periods=n, freq="D")
    values = [start + i * step for i in range(n)]
    return pd.Series(values, index=idx)


def test_compute_technical_metrics_bullish_trend_and_positive_return():
    close = _rising_series(260)
    metrics = compute_technical_metrics("AAA.NS", "AAA Ltd", close)
    assert metrics is not None
    assert metrics.trend == "Bullish"
    assert metrics.return_1y_pct > 0
    assert metrics.last_price_inr == round(close.iloc[-1], 2)


def test_compute_technical_metrics_empty_series_returns_none():
    assert compute_technical_metrics("AAA.NS", "AAA Ltd", pd.Series(dtype=float)) is None


def test_compute_technical_metrics_zero_start_price_returns_none():
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    close = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0], index=idx)
    assert compute_technical_metrics("AAA.NS", "AAA Ltd", close) is None


def test_shape_fundamentals_formats_known_fields():
    info = {
        "marketCap": 123456789,
        "trailingPE": 15.678,
        "priceToBook": 2.5,
        "debtToEquity": 40.0,
        "returnOnEquity": 0.185,
        "trailingEps": 12.3,
        "dividendYield": 0.021,
    }
    result = _shape_fundamentals(info)
    assert result["market_cap_cr"] == "123,456,789"
    assert result["pe_ratio"] == "15.68"
    assert result["roe"] == "18.50%"
    assert result["dividend_yield"] == "2.10%"
    assert result["expense_ratio"] == "N/A"


def test_shape_fundamentals_missing_fields_are_na():
    assert _shape_fundamentals({}) == {
        "market_cap_cr": "N/A",
        "pe_ratio": "N/A",
        "pb_ratio": "N/A",
        "debt_to_equity": "N/A",
        "roe": "N/A",
        "eps_ttm": "N/A",
        "dividend_yield": "N/A",
        "expense_ratio": "N/A",
    }
