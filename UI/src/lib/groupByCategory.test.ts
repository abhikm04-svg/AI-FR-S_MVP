import { describe, expect, it } from "vitest";
import type { AssetMetrics } from "./apiClient";
import { groupByInstrumentType } from "./groupByCategory";

function metric(ticker: string, instrument_type?: string): AssetMetrics {
  return {
    ticker,
    name: ticker,
    last_price_inr: 100,
    return_1y_pct: 10,
    volatility_pct: 15,
    sharpe_ratio: 1,
    trend: "Bullish",
    market_cap_cr: "N/A",
    pe_ratio: "N/A",
    pb_ratio: "N/A",
    debt_to_equity: "N/A",
    roe: "N/A",
    eps_ttm: "N/A",
    dividend_yield: "N/A",
    expense_ratio: "N/A",
    instrument_type,
  };
}

describe("groupByInstrumentType", () => {
  it("produces one group per distinct category, in first-seen order", () => {
    const groups = groupByInstrumentType([
      metric("A", "Stocks"),
      metric("B", "Mutual Funds/ETFs"),
      metric("C", "Stocks"),
    ]);
    expect(Array.from(groups.keys())).toEqual(["Stocks", "Mutual Funds/ETFs"]);
    expect(groups.get("Stocks")?.map((m) => m.ticker)).toEqual(["A", "C"]);
  });

  it("falls back to Other when instrument_type is missing (pre-existing sessions)", () => {
    const groups = groupByInstrumentType([metric("A", undefined)]);
    expect(Array.from(groups.keys())).toEqual(["Other"]);
  });

  it("column count matches the number of distinct categories present", () => {
    const two = groupByInstrumentType([metric("A", "Stocks"), metric("B", "Gold/Commodities")]);
    expect(two.size).toBe(2);

    const three = groupByInstrumentType([
      metric("A", "Stocks"),
      metric("B", "Gold/Commodities"),
      metric("C", "Mutual Funds/ETFs"),
    ]);
    expect(three.size).toBe(3);
  });
});
