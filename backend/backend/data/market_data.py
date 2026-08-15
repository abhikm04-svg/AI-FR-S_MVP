"""Consolidated replacement for the two Streamlit copies' FinancialTools
class. No Streamlit imports: caching is an explicit TTLCache, progress is
returned/logged rather than a UI side effect. Mutual fund price history now
comes from the batched Supabase read (repository.nav_prices) instead of a
live mftool call per scheme -- that's the actual N+1 fix from plan.md
Section 2, consumed here.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Optional

import asyncpg
import numpy as np
import pandas as pd
import yfinance as yf
from cachetools import TTLCache
from nselib import capital_market

from backend.data.models import AssetMetrics, AssetRef
from backend.repository.nav_prices import get_nav_prices_batch

_CACHE_TTL_SECONDS = 3600
_nse_cache: TTLCache = TTLCache(maxsize=8, ttl=_CACHE_TTL_SECONDS)

RISK_FREE_RATE = 0.06


# ---------------------------------------------------------------------------
# NSE universe discovery (stocks/ETFs) -- unchanged logic from FinancialTools,
# cached in-process since equity/ETF caching in Postgres was explicitly
# deferred (plan.md decisions).
# ---------------------------------------------------------------------------


async def get_all_nse_stocks() -> dict[str, str]:
    """{ticker: name} for all NSE equities."""
    if "nse_stocks" in _nse_cache:
        return _nse_cache["nse_stocks"]

    def _fetch() -> dict[str, str]:
        df = capital_market.equity_list()
        if "SYMBOL" not in df.columns:
            return {}
        mapping: dict[str, str] = {}
        for _, row in df.iterrows():
            ticker = f"{row['SYMBOL']}.NS"
            name = row.get("NAME OF COMPANY", row["SYMBOL"]).title()
            mapping[ticker] = name
        return mapping

    result = await asyncio.to_thread(_fetch)
    _nse_cache["nse_stocks"] = result
    return result


async def get_nifty500_assets(stock_map: dict[str, str]) -> list[AssetRef]:
    """Prioritized NIFTY 500 assets, falling back to the first 500 known
    stocks if the NIFTY 500 list itself can't be fetched."""

    def _fetch() -> Optional[list[str]]:
        try:
            nifty_500 = capital_market.nifty500_equity_list()
            col = "Symbol" if "Symbol" in nifty_500.columns else "SYMBOL"
            return [f"{sym}.NS" for sym in nifty_500[col].tolist()]
        except Exception:
            return None

    targets = await asyncio.to_thread(_fetch)
    if targets is None:
        targets = list(stock_map.keys())[:500]

    return [AssetRef(ticker=t, name=stock_map.get(t, t.replace(".NS", ""))) for t in targets]


async def get_all_etfs() -> dict[str, str]:
    """{ticker: name} for listed ETFs, found by diffing bhavcopy-traded
    EQ-series symbols against the known equity list."""
    if "etfs" in _nse_cache:
        return _nse_cache["etfs"]

    def _fetch() -> dict[str, str]:
        equity_df = capital_market.equity_list()
        equity_symbols = set(equity_df["SYMBOL"]) if "SYMBOL" in equity_df.columns else set()

        bhav_df = pd.DataFrame()
        for i in range(5):
            date_check = (datetime.now() - timedelta(days=i)).strftime("%d-%m-%Y")
            try:
                bhav_df = capital_market.bhav_copy_with_delivery(date_check)
                if not bhav_df.empty:
                    break
            except Exception:
                continue

        if bhav_df.empty or "SERIES" not in bhav_df.columns or "SYMBOL" not in bhav_df.columns:
            return {}

        traded_symbols = set(bhav_df[bhav_df["SERIES"] == "EQ"]["SYMBOL"])
        etf_symbols = traded_symbols - equity_symbols
        return {f"{sym}.NS": f"{sym} (ETF)" for sym in etf_symbols}

    result = await asyncio.to_thread(_fetch)
    _nse_cache["etfs"] = result
    return result


async def get_asset_universe(
    instruments: list[str], mf_schemes: dict[str, str]
) -> list[AssetRef]:
    """Maps user instrument-category selections to a candidate asset list.
    mf_schemes is the Direct+Growth catalog, already loaded from the DB by
    the caller (repository.schemes.get_direct_growth_schemes) -- this
    function does not touch the database itself.
    """
    assets: dict[str, AssetRef] = {}

    if "Stocks" in instruments:
        stock_map = await get_all_nse_stocks()
        for ref in await get_nifty500_assets(stock_map):
            assets[ref.ticker] = ref

    if "Mutual Funds/ETFs" in instruments:
        for ticker, name in (await get_all_etfs()).items():
            assets[ticker] = AssetRef(ticker=ticker, name=name)
        for code, name in mf_schemes.items():
            assets[code] = AssetRef(ticker=code, name=name)

    if "Gold/Commodities" in instruments:
        for ticker, name in (await get_all_etfs()).items():
            if "GOLD" in ticker or "SILVER" in ticker:
                assets[ticker] = AssetRef(ticker=ticker, name=name)

    return list(assets.values())


# ---------------------------------------------------------------------------
# Price history: yfinance for stocks/ETFs, batched Supabase read for MFs.
# ---------------------------------------------------------------------------


def _period_to_days(period: str) -> int:
    if period == "5y":
        return 365 * 5
    if period == "max":
        return 365 * 100
    return 365


async def fetch_stock_history(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()

    def _fetch() -> pd.DataFrame:
        return yf.download(tickers, period=period, group_by="ticker", progress=False)

    return await asyncio.to_thread(_fetch)


def _series_from_yf(yf_data: pd.DataFrame, ticker: str) -> Optional[pd.Series]:
    if yf_data.empty:
        return None
    if isinstance(yf_data.columns, pd.MultiIndex):
        try:
            df = yf_data[ticker]
        except KeyError:
            return None
    else:
        if "Close" not in yf_data.columns:
            return None
        df = yf_data
    if "Close" not in df.columns:
        return None
    return df["Close"].dropna()


def _series_from_nav_rows(rows: Iterable[tuple[date, Decimal]]) -> pd.Series:
    rows = list(rows)
    if not rows:
        return pd.Series(dtype=float)
    dates, navs = zip(*rows)
    return pd.Series([float(n) for n in navs], index=pd.to_datetime(list(dates))).sort_index()


async def fetch_market_data(
    pool: asyncpg.Pool, tickers: list[str], period: str = "1y"
) -> dict[str, pd.Series]:
    """Fetches price history for a mixed list of tickers -- yfinance for
    stocks/ETFs (strings containing '.NS'), the batched Supabase read
    (repository.nav_prices.get_nav_prices_batch) for mutual funds (numeric
    scheme codes). Returns {ticker: close_price_series}. This single batched
    call replaces the old per-scheme-code loop entirely.
    """
    if not tickers:
        return {}

    yf_tickers = [t for t in tickers if isinstance(t, str) and ".NS" in t]
    mf_codes = [t for t in tickers if isinstance(t, str) and t.isdigit()]

    series: dict[str, pd.Series] = {}

    if yf_tickers:
        yf_data = await fetch_stock_history(yf_tickers, period=period)
        for ticker in yf_tickers:
            close = _series_from_yf(yf_data, ticker)
            if close is not None and not close.empty:
                series[ticker] = close

    if mf_codes:
        since = date.today() - timedelta(days=_period_to_days(period))
        nav_rows = await get_nav_prices_batch(pool, mf_codes, since)
        for code, rows in nav_rows.items():
            close = _series_from_nav_rows(rows)
            if not close.empty:
                series[code] = close

    return series


# ---------------------------------------------------------------------------
# Technical + fundamental metrics -- ported from
# FinancialTools.calculate_technical_metrics/fetch_fundamentals, decoupled
# from data source (works identically for yfinance- and NAV-derived series).
# ---------------------------------------------------------------------------


def compute_technical_metrics(ticker: str, name: str, close: pd.Series) -> Optional[AssetMetrics]:
    close = close.dropna()
    if close.empty:
        return None

    current_price = close.iloc[-1]
    start_price = close.iloc[0]
    if start_price == 0:
        return None

    daily_return = close.pct_change()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean()

    volatility = daily_return.std() * np.sqrt(252)
    total_return = (current_price - start_price) / start_price

    sharpe_ratio = (total_return - RISK_FREE_RATE) / volatility if volatility else 0.0
    trend = "Bullish" if sma_50.iloc[-1] > sma_200.iloc[-1] else "Bearish"

    return AssetMetrics(
        ticker=ticker,
        name=name,
        last_price_inr=round(float(current_price), 2),
        return_1y_pct=round(float(total_return) * 100, 2),
        volatility_pct=round(float(volatility) * 100, 2),
        sharpe_ratio=round(float(sharpe_ratio), 2),
        trend=trend,
    )


def _shape_fundamentals(info: dict) -> dict[str, str]:
    def get_val(key: str, fmt: str = "{:.2f}") -> str:
        val = info.get(key)
        if val is None:
            return "N/A"
        if isinstance(val, (int, float)):
            return fmt.format(val)
        return str(val)

    def get_pct(key: str) -> str:
        val = info.get(key)
        if val is None:
            return "N/A"
        return f"{val * 100:.2f}%"

    return {
        "market_cap_cr": get_val("marketCap", "{:,.0f}"),
        "pe_ratio": get_val("trailingPE"),
        "pb_ratio": get_val("priceToBook"),
        "debt_to_equity": get_val("debtToEquity"),
        "roe": get_pct("returnOnEquity"),
        "eps_ttm": get_val("trailingEps"),
        "dividend_yield": get_pct("dividendYield"),
        "expense_ratio": get_val("annualReportExpenseRatio") if "annualReportExpenseRatio" in info else "N/A",
    }


async def fetch_fundamentals(ticker: str) -> dict[str, str]:
    def _fetch() -> dict:
        try:
            return yf.Ticker(ticker).info
        except Exception:
            return {}

    info = await asyncio.to_thread(_fetch)
    return _shape_fundamentals(info)
