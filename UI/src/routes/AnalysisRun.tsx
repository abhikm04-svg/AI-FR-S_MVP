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
    <div>
      <h1>🕵️ Agent Workflow: Analysis</h1>
      <AgentProgressCard
        icon="🕵️"
        name="Chanakya"
        role="Market Researcher"
        description="Scanning NSE/BSE markets for stocks, ETFs, and mutual funds…"
        variant="researcher"
        state={cards.researcher}
      />
      <AgentProgressCard
        icon="👩‍💻"
        name="Aryabhata"
        role="Financial Analyst"
        description="Running volatility analysis, Sharpe ratios, and fundamentals…"
        variant="analyst"
        state={cards.analyst}
      />
      <AgentProgressCard
        icon="🧑‍💼"
        name="Tagore"
        role="Business Analyst"
        description="Drafting the investment thesis…"
        variant="reporter"
        state={cards.reporter}
      />

      {sessionStatus === "failed" && (
        <p role="alert">
          Analysis yielded no results. Try broadening your criteria or changing your risk
          appetite.
        </p>
      )}
    </div>
  );
}
