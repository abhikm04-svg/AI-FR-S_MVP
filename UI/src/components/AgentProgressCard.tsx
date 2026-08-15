import type { CardState } from "../lib/agentStates";

interface AgentProgressCardProps {
  icon: string;
  name: string;
  role: string;
  description: string;
  variant: "researcher" | "analyst" | "reporter";
  state: CardState;
}

const STATE_LABEL: Record<CardState, string> = {
  pending: "Waiting…",
  active: "Working…",
  done: "Done",
  error: "No matches found",
};

export function AgentProgressCard({ icon, name, role, description, variant, state }: AgentProgressCardProps) {
  const classNames = ["agent-box", variant];
  if (state === "pending") classNames.push("pending");
  if (state === "error") classNames.push("error");

  return (
    <div className={classNames.join(" ")} data-state={state}>
      <div className="agent-title">
        <span aria-hidden="true">{icon}</span>
        <span>
          {name} ({role})
        </span>
      </div>
      <p>{description}</p>
      <p>
        <strong>{STATE_LABEL[state]}</strong>
      </p>
    </div>
  );
}
