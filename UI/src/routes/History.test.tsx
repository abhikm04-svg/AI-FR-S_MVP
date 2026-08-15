import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { useSessionList } from "../hooks/useSessions";
import { History } from "./History";

vi.mock("../hooks/useSessions", () => ({
  useSessionList: vi.fn(),
}));

describe("History", () => {
  it("shows an empty state when there are no sessions", () => {
    vi.mocked(useSessionList).mockReturnValue({ data: [], isLoading: false } as never);
    render(<History />, { wrapper: MemoryRouter });
    expect(screen.getByText(/No past analysis runs yet/)).toBeInTheDocument();
  });

  it("lists past sessions with a link to their results", () => {
    vi.mocked(useSessionList).mockReturnValue({
      data: [
        {
          id: "s1",
          thread_id: "t1",
          goal: "Wealth Creation",
          status: "completed",
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
    } as never);
    render(<History />, { wrapper: MemoryRouter });
    expect(screen.getByText("Wealth Creation")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View" })).toHaveAttribute("href", "/results/s1");
  });
});
