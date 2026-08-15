import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricsTable } from "./MetricsTable";
import type { AssetMetrics } from "../lib/apiClient";

const METRIC: AssetMetrics = {
  ticker: "AAA.NS",
  name: "Alpha Fund",
  last_price_inr: 123.456,
  return_1y_pct: 12.3,
  volatility_pct: 15.6,
  sharpe_ratio: 1.23,
  trend: "Bullish",
  market_cap_cr: "N/A",
  pe_ratio: "18.20",
  pb_ratio: "N/A",
  debt_to_equity: "N/A",
  roe: "15.00%",
  eps_ttm: "N/A",
  dividend_yield: "N/A",
  expense_ratio: "N/A",
};

describe("MetricsTable", () => {
  it("shows a fallback message when there are no metrics", () => {
    render(<MetricsTable metrics={[]} />);
    expect(screen.getByText("No metrics available.")).toBeInTheDocument();
  });

  it("renders a row per asset with formatted values", () => {
    render(<MetricsTable metrics={[METRIC]} />);
    expect(screen.getByText("Alpha Fund")).toBeInTheDocument();
    expect(screen.getByText("₹123.46")).toBeInTheDocument();
    expect(screen.getByText("12.30%")).toBeInTheDocument();
    expect(screen.getByText("18.20")).toBeInTheDocument();
  });
});
