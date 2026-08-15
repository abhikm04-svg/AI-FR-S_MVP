import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useSessionDetail, usePriceHistory } from "../hooks/useSessions";
import type { SessionDetail } from "../lib/apiClient";
import { Results } from "./Results";

vi.mock("react-router-dom", () => ({
  useParams: () => ({ sessionId: "session-1" }),
}));

vi.mock("../hooks/useSessions", () => ({
  useSessionDetail: vi.fn(),
  usePriceHistory: vi.fn(),
}));

describe("Results", () => {
  it("shows a loading state before data arrives", () => {
    vi.mocked(useSessionDetail).mockReturnValue({ data: undefined, isLoading: true } as never);
    vi.mocked(usePriceHistory).mockReturnValue({ data: undefined } as never);
    render(<Results />);
    expect(screen.getByText("Loading results…")).toBeInTheDocument();
  });

  it("renders the thesis and metrics once loaded", () => {
    const session: SessionDetail = {
      id: "session-1",
      thread_id: "t1",
      goal: "Wealth Creation",
      status: "completed",
      error_message: null,
      created_at: "2026-01-01T00:00:00Z",
      final_thesis: "# Executive Summary\n\nGood picks ahead.",
      analyzed_metrics: [
        {
          ticker: "AAA.NS",
          name: "Alpha Fund",
          last_price_inr: 100,
          return_1y_pct: 10,
          volatility_pct: 12,
          sharpe_ratio: 1.1,
          trend: "Bullish",
          market_cap_cr: "N/A",
          pe_ratio: "N/A",
          pb_ratio: "N/A",
          debt_to_equity: "N/A",
          roe: "N/A",
          eps_ttm: "N/A",
          dividend_yield: "N/A",
          expense_ratio: "N/A",
        },
      ],
    };
    vi.mocked(useSessionDetail).mockReturnValue({ data: session, isLoading: false } as never);
    vi.mocked(usePriceHistory).mockReturnValue({ data: {} } as never);

    render(<Results />);
    expect(screen.getByRole("heading", { name: "Executive Summary" })).toBeInTheDocument();
    expect(screen.getByText("Alpha Fund")).toBeInTheDocument();
  });
});
