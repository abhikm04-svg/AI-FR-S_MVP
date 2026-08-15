import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AgentProgressCard } from "./AgentProgressCard";

describe("AgentProgressCard", () => {
  it("renders the agent name, role, and pending label", () => {
    render(
      <AgentProgressCard
        icon="🕵️"
        name="Chanakya"
        role="Market Researcher"
        description="Scans NSE/BSE for stocks, ETFs, and Gold."
        variant="researcher"
        state="pending"
      />,
    );
    expect(screen.getByText(/Chanakya/)).toBeInTheDocument();
    expect(screen.getByText(/Market Researcher/)).toBeInTheDocument();
    expect(screen.getByText("Waiting…")).toBeInTheDocument();
  });

  it("shows the error label when state is error", () => {
    render(
      <AgentProgressCard
        icon="👩‍💻"
        name="Aryabhata"
        role="Financial Analyst"
        description="Runs mathematical models & backtests."
        variant="analyst"
        state="error"
      />,
    );
    expect(screen.getByText("No matches found")).toBeInTheDocument();
  });
});
