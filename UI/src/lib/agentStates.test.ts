import { describe, expect, it } from "vitest";
import { deriveCardStates } from "./agentStates";

describe("deriveCardStates", () => {
  it("all pending while the session hasn't started", () => {
    expect(deriveCardStates(null, "pending")).toEqual({
      researcher: "pending",
      analyst: "pending",
      reporter: "pending",
    });
  });

  it("researcher active once running with no node status yet", () => {
    expect(deriveCardStates(null, "running")).toEqual({
      researcher: "active",
      analyst: "pending",
      reporter: "pending",
    });
  });

  it("analyst active once researcher completes", () => {
    expect(deriveCardStates("analyzing", "running")).toEqual({
      researcher: "done",
      analyst: "active",
      reporter: "pending",
    });
  });

  it("reporter active once analyst completes", () => {
    expect(deriveCardStates("reporting", "running")).toEqual({
      researcher: "done",
      analyst: "done",
      reporter: "active",
    });
  });

  it("all done when the run finishes successfully", () => {
    expect(deriveCardStates("done", "completed")).toEqual({
      researcher: "done",
      analyst: "done",
      reporter: "done",
    });
  });

  it("analyst shows error when no assets matched the risk profile", () => {
    expect(deriveCardStates("error", "failed")).toEqual({
      researcher: "done",
      analyst: "error",
      reporter: "pending",
    });
  });
});
