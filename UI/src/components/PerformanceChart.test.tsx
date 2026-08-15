import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PerformanceChart, buildChartRows } from "./PerformanceChart";

describe("buildChartRows", () => {
  it("merges multiple tickers onto rows keyed by date", () => {
    const rows = buildChartRows({
      A: [
        { date: "2024-01-01", value: 100 },
        { date: "2024-01-02", value: 101 },
      ],
      B: [{ date: "2024-01-01", value: 100 }],
    });
    expect(rows).toEqual([
      { date: "2024-01-01", A: 100, B: 100 },
      { date: "2024-01-02", A: 101 },
    ]);
  });

  it("returns an empty array for no series", () => {
    expect(buildChartRows({})).toEqual([]);
  });
});

describe("PerformanceChart", () => {
  it("shows a fallback message when there is no data", () => {
    render(<PerformanceChart series={{}} />);
    expect(screen.getByText(/No price history available/)).toBeInTheDocument();
  });

  it("renders a chart heading when data is present", () => {
    render(
      <PerformanceChart
        series={{ AAA: [{ date: "2024-01-01", value: 100 }] }}
        names={{ AAA: "Alpha Fund" }}
      />,
    );
    expect(screen.getByText("Comparative Performance (Normalized)")).toBeInTheDocument();
  });
});
