import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAnalysisStream } from "./useAnalysisStream";

class MockEventSource {
  static instances: MockEventSource[] = [];
  listeners: Record<string, EventListener[]> = {};
  closed = false;

  constructor(public url: string) {
    MockEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: EventListener) {
    (this.listeners[type] ??= []).push(listener);
  }

  emit(type: string, data: unknown) {
    for (const listener of this.listeners[type] ?? []) {
      listener({ data: JSON.stringify(data) } as MessageEvent);
    }
  }

  close() {
    this.closed = true;
  }
}

beforeEach(() => {
  MockEventSource.instances = [];
  vi.stubGlobal("EventSource", MockEventSource);
});

describe("useAnalysisStream", () => {
  it("returns null before any event arrives", () => {
    const { result } = renderHook(() => useAnalysisStream("session-1"));
    expect(result.current).toBeNull();
  });

  it("updates status from a status event", () => {
    const { result } = renderHook(() => useAnalysisStream("session-1"));
    const source = MockEventSource.instances[0];
    act(() => {
      source.emit("status", { session_status: "running", node_status: "researching" });
    });
    expect(result.current).toEqual({ sessionStatus: "running", nodeStatus: "researching" });
  });

  it("closes the connection once the session completes", () => {
    renderHook(() => useAnalysisStream("session-1"));
    const source = MockEventSource.instances[0];
    act(() => {
      source.emit("status", { session_status: "completed", node_status: null });
    });
    expect(source.closed).toBe(true);
  });

  it("does nothing when sessionId is undefined", () => {
    renderHook(() => useAnalysisStream(undefined));
    expect(MockEventSource.instances).toHaveLength(0);
  });
});
