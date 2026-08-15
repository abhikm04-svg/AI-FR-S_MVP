export type CardState = "pending" | "active" | "done" | "error";

export interface AgentCardStates {
  researcher: CardState;
  analyst: CardState;
  reporter: CardState;
}

const IDLE: AgentCardStates = { researcher: "pending", analyst: "pending", reporter: "pending" };

/** Maps the graph's fine-grained node status (researching/analyzing/
 * reporting/done/error) onto the three agent progress cards. */
export function deriveCardStates(nodeStatus: string | null, sessionStatus: string): AgentCardStates {
  if (sessionStatus === "pending") return IDLE;

  switch (nodeStatus) {
    case "analyzing":
      return { researcher: "done", analyst: "active", reporter: "pending" };
    case "reporting":
      return { researcher: "done", analyst: "done", reporter: "active" };
    case "done":
      return { researcher: "done", analyst: "done", reporter: "done" };
    case "error":
      return { researcher: "done", analyst: "error", reporter: "pending" };
    case "researching":
    default:
      // sessionStatus is running/completed/failed but the graph hasn't
      // reported a node status yet -- treat as still on the first step.
      return { researcher: "active", analyst: "pending", reporter: "pending" };
  }
}
