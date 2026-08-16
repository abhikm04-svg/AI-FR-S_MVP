import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { AgentProgressCard } from "../components/AgentProgressCard";
import { useAnalysisStream } from "../hooks/useAnalysisStream";
import { deriveCardStates } from "../lib/agentStates";

export function AnalysisRun() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const stream = useAnalysisStream(sessionId);

  const sessionStatus = stream?.sessionStatus ?? "pending";
  const nodeStatus = stream?.nodeStatus ?? null;
  const cards = deriveCardStates(nodeStatus, sessionStatus);

  useEffect(() => {
    if (sessionStatus === "completed" && sessionId) {
      navigate(`/results/${sessionId}`);
    }
  }, [sessionStatus, sessionId, navigate]);

  return (
    <div className="w-full">
      <h1 className="text-3xl font-headline font-semibold text-on-surface tracking-tight mb-1 text-center">
        Agent Workflow: Analysis
      </h1>
      <p className="text-on-surface-variant text-sm mb-10 text-center max-w-2xl mx-auto">
        Our AI agents are currently processing your request. Please hold while we compile the
        necessary data and formulate the investment thesis.
      </p>

      <div className="flex flex-col lg:flex-row lg:items-stretch gap-0 lg:gap-6">
        <div className="flex-1">
          <AgentProgressCard
            icon="travel_explore"
            name="Chanakya"
            role="Market Researcher"
            description="Scanning NSE/BSE markets for stocks, ETFs, and mutual funds…"
            variant="researcher"
            state={cards.researcher}
          />
        </div>
        <div className="stepper-connector lg:hidden" />
        <div
          aria-hidden="true"
          className="hidden lg:flex items-center justify-center text-on-surface-variant/40 material-symbols-outlined"
        >
          arrow_forward
        </div>
        <div className="flex-1">
          <AgentProgressCard
            icon="calculate"
            name="Aryabhata"
            role="Financial Analyst"
            description="Running volatility analysis, Sharpe ratios, and fundamentals…"
            variant="analyst"
            state={cards.analyst}
          />
        </div>
        <div className="stepper-connector lg:hidden" />
        <div
          aria-hidden="true"
          className="hidden lg:flex items-center justify-center text-on-surface-variant/40 material-symbols-outlined"
        >
          arrow_forward
        </div>
        <div className="flex-1">
          <AgentProgressCard
            icon="description"
            name="Tagore"
            role="Business Analyst"
            description="Drafting the investment thesis…"
            variant="reporter"
            state={cards.reporter}
          />
        </div>
      </div>

      {sessionStatus === "failed" && (
        <p role="alert" className="text-error text-sm mt-5 text-center">
          Analysis yielded no results. Try broadening your criteria or changing your risk
          appetite.
        </p>
      )}

      <div className="flex justify-center mt-6">
        <button
          type="button"
          disabled
          title="Not yet supported"
          className="px-5 py-2 rounded-xl border border-outline-variant text-on-surface-variant text-sm opacity-50 cursor-not-allowed"
        >
          Cancel Analysis
        </button>
      </div>
    </div>
  );
}
