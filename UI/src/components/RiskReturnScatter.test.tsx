import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RiskReturnScatter, bubbleSize } from "./RiskReturnScatter";
import type { AssetMetrics } from "../lib/apiClient";

function metric(overrides: Partial<AssetMetrics> = {}): AssetMetrics {
  return {
    ticker: "AAA.NS",
    name: "Alpha Fund",
    last_price_inr: 100,
    return_1y_pct: 12,
    volatility_pct: 15,
    sharpe_ratio: 1.2,
    trend: "Bullish",
    market_cap_cr: "N/A",
    pe_ratio: "N/A",
    pb_ratio: "N/A",
    debt_to_equity: "N/A",
    roe: "N/A",
    eps_ttm: "N/A",
    dividend_yield: "N/A",
    expense_ratio: "N/A",
    ...overrides,
  };
}

describe("bubbleSize", () => {
  it("uses the sharpe ratio when positive", () => {
    expect(bubbleSize(metric({ sharpe_ratio: 2.5 }))).toBe(2.5);
  });

  it("floors negative sharpe ratios to a small positive value", () => {
    expect(bubbleSize(metric({ sharpe_ratio: -1.5 }))).toBe(0.01);
  });
});

describe("RiskReturnScatter", () => {
  it("shows a fallback message when there are no assets", () => {
    render(<RiskReturnScatter metrics={[]} />);
    expect(screen.getByText("No assets to plot.")).toBeInTheDocument();
  });

  it("renders the chart heading when assets are present", () => {
    render(<RiskReturnScatter metrics={[metric()]} />);
    expect(screen.getByText("Risk vs Reward Landscape")).toBeInTheDocument();
  });
});
