import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createSession, startRun } from "../lib/apiClient";
import { ProfileSetup } from "./ProfileSetup";

vi.mock("../lib/apiClient", () => ({
  createSession: vi.fn(),
  startRun: vi.fn(),
  getUserId: () => "test-user",
}));

function renderWithProviders(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ProfileSetup", () => {
  beforeEach(() => vi.clearAllMocks());

  it("submit is disabled and an alert shows when no instruments are selected", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfileSetup />);

    await user.click(screen.getByLabelText("Stocks"));
    await user.click(screen.getByLabelText("Mutual Funds/ETFs"));

    expect(screen.getByRole("alert")).toHaveTextContent("Select at least one investment type.");
    expect(screen.getByRole("button", { name: /Analyze Market/ })).toBeDisabled();
  });

  it("submitting creates a session and starts a run with the chosen profile", async () => {
    const user = userEvent.setup();
    vi.mocked(createSession).mockResolvedValue({ id: "session-1", thread_id: "t1", status: "pending" });
    vi.mocked(startRun).mockResolvedValue({ status: "started" });

    renderWithProviders(<ProfileSetup />);

    await user.click(screen.getByRole("button", { name: /Analyze Market/ }));

    await waitFor(() => expect(createSession).toHaveBeenCalledTimes(1));
    expect(createSession).toHaveBeenCalledWith(
      expect.objectContaining({
        instruments: ["Stocks", "Mutual Funds/ETFs"],
        risk: "Moderate",
        horizon: "Long Term (5+ yrs)",
        goal: "Wealth Creation",
      }),
    );
    await waitFor(() => expect(startRun).toHaveBeenCalledWith("session-1"));
  });

  it("switching to range selection sends a [start, end] risk tuple", async () => {
    const user = userEvent.setup();
    vi.mocked(createSession).mockResolvedValue({ id: "session-1", thread_id: "t1", status: "pending" });
    vi.mocked(startRun).mockResolvedValue({ status: "started" });

    renderWithProviders(<ProfileSetup />);

    await user.click(screen.getByLabelText("Allow Range Selection"));
    await user.click(screen.getByRole("button", { name: /Analyze Market/ }));

    await waitFor(() => expect(createSession).toHaveBeenCalledTimes(1));
    expect(createSession).toHaveBeenCalledWith(
      expect.objectContaining({ risk: ["Conservative", "Moderate"] }),
    );
  });
});
