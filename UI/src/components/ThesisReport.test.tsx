import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThesisReport } from "./ThesisReport";

describe("ThesisReport", () => {
  it("shows a fallback message for empty input", () => {
    render(<ThesisReport thesis="" />);
    expect(screen.getByText("No thesis generated yet.")).toBeInTheDocument();
  });

  it("renders markdown headings and bold text", () => {
    render(<ThesisReport thesis={"# Executive Summary\n\n**Top pick:** Alpha Fund"} />);
    expect(screen.getByRole("heading", { name: "Executive Summary" })).toBeInTheDocument();
    expect(screen.getByText("Top pick:")).toBeInTheDocument();
  });
});
