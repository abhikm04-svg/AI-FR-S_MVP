import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAnalysisStream } from "../hooks/useAnalysisStream";
import { AnalysisRun } from "./AnalysisRun";

const mockNavigate = vi.fn();

vi.mock("react-router-dom", () => ({
  useParams: () => ({ sessionId: "session-1" }),
  useNavigate: () => mockNavigate,
}));

vi.mock("../hooks/useAnalysisStream", () => ({
  useAnalysisStream: vi.fn(),
}));

describe("AnalysisRun", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    vi.mocked(useAnalysisStream).mockReset();
  });

  it("shows all cards pending before the stream reports anything", () => {
    vi.mocked(useAnalysisStream).mockReturnValue(null);
    render(<AnalysisRun />);
    expect(screen.getAllByText("Waiting…")).toHaveLength(3);
  });

  it("marks the researcher card active once the graph starts researching", () => {
    vi.mocked(useAnalysisStream).mockReturnValue({ sessionStatus: "running", nodeStatus: "researching" });
    render(<AnalysisRun />);
    expect(screen.getAllByText("Working…")).toHaveLength(1);
  });

  it("navigates to the results page once the session completes", () => {
    vi.mocked(useAnalysisStream).mockReturnValue({ sessionStatus: "completed", nodeStatus: "done" });
    render(<AnalysisRun />);
    expect(mockNavigate).toHaveBeenCalledWith("/results/session-1");
  });

  it("shows a failure message when the session fails", () => {
    vi.mocked(useAnalysisStream).mockReturnValue({ sessionStatus: "failed", nodeStatus: "error" });
    render(<AnalysisRun />);
    expect(screen.getByRole("alert")).toHaveTextContent("Analysis yielded no results");
  });
});
