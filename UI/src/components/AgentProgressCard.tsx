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

const VARIANT_BORDER: Record<AgentProgressCardProps["variant"], string> = {
  researcher: "border-l-primary",
  analyst: "border-l-secondary",
  reporter: "border-l-tertiary",
};

const VARIANT_SEAL: Record<AgentProgressCardProps["variant"], string> = {
  researcher: "var(--color-primary)",
  analyst: "var(--color-secondary)",
  reporter: "var(--color-tertiary)",
};

const VARIANT_ORDINAL: Record<AgentProgressCardProps["variant"], string> = {
  researcher: "I",
  analyst: "II",
  reporter: "III",
};

const ICON_COLOR_CLASS: Record<CardState, string> = {
  pending: "text-on-surface-variant",
  active: "text-primary",
  done: "text-success",
  error: "text-error",
};

export function AgentProgressCard({ icon, name, role, description, variant, state }: AgentProgressCardProps) {
  return (
    <div
      data-state={state}
      className={`relative p-5 rounded-xl border border-outline-variant/40 border-l-4 bg-surface-container-low shadow-sm ${VARIANT_BORDER[variant]} ${
        state === "pending" ? "opacity-55" : ""
      } ${state === "active" ? "shadow-[0_0_0_1px_var(--color-primary)]" : ""}`}
    >
      <div className="flex items-center gap-3 font-headline font-semibold text-lg mb-2">
        <span
          className={`agent-seal w-9 h-9 ${ICON_COLOR_CLASS[state]}`}
          style={{ ["--seal" as string]: VARIANT_SEAL[variant] }}
          aria-hidden="true"
        >
          <span className={`material-symbols-outlined text-lg ${state === "active" ? "animate-spin" : ""}`}>
            {state === "active" ? "progress_activity" : state === "done" ? "check" : state === "error" ? "error" : icon}
          </span>
        </span>
        <span className="flex-1">
          {name} ({role})
        </span>
        <span
          aria-hidden="true"
          className="font-mono text-xs text-on-surface-variant tracking-widest"
        >
          {VARIANT_ORDINAL[variant]}
        </span>
      </div>
      <p className="text-sm text-on-surface-variant">{description}</p>
      {state === "active" && (
        <div className="indeterminate-bar mt-3" role="progressbar" aria-label={`${name} working`} />
      )}
      <p className="text-sm font-semibold mt-2">{STATE_LABEL[state]}</p>
    </div>
  );
}
