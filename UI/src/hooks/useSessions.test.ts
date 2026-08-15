import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createSession, listSessions, startRun } from "../lib/apiClient";
import { useCreateSession, useSessionList } from "./useSessions";

vi.mock("../lib/apiClient", () => ({
  listSessions: vi.fn(),
  createSession: vi.fn(),
  startRun: vi.fn(),
  getUserId: () => "test-user",
}));

function createWrapper() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client }, children);
}

describe("useSessionList", () => {
  beforeEach(() => vi.clearAllMocks());

  it("fetches and returns the session list", async () => {
    vi.mocked(listSessions).mockResolvedValue([
      { id: "1", thread_id: "t1", goal: "Wealth Creation", status: "completed", created_at: "2026-01-01" },
    ]);
    const { result } = renderHook(() => useSessionList(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });
});

describe("useCreateSession", () => {
  beforeEach(() => vi.clearAllMocks());

  it("creates a session then immediately triggers a run", async () => {
    vi.mocked(createSession).mockResolvedValue({ id: "s1", thread_id: "t1", status: "pending" });
    vi.mocked(startRun).mockResolvedValue({ status: "started" });

    const { result } = renderHook(() => useCreateSession(), { wrapper: createWrapper() });
    result.current.mutate({
      instruments: ["Stocks"],
      risk: "Moderate",
      target_return: "12",
      horizon: "Long Term (5+ yrs)",
      goal: "Wealth Creation",
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(createSession).toHaveBeenCalledTimes(1);
    expect(startRun).toHaveBeenCalledWith("s1");
  });
});
