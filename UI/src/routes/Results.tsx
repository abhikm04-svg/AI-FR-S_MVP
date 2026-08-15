import { useParams } from "react-router-dom";
import { MetricsTable } from "../components/MetricsTable";
import { PerformanceChart } from "../components/PerformanceChart";
import { RiskReturnScatter } from "../components/RiskReturnScatter";
import { ThesisReport } from "../components/ThesisReport";
import { usePriceHistory, useSessionDetail } from "../hooks/useSessions";

export function Results() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: session, isLoading } = useSessionDetail(sessionId);
  const { data: priceHistory } = usePriceHistory(sessionId);

  if (isLoading || !session) {
    return <p>Loading results…</p>;
  }

  const metrics = session.analyzed_metrics ?? [];
  const names = Object.fromEntries(metrics.map((m) => [m.ticker, m.name]));

  return (
    <div>
      <h1>📈 Final Investment Report</h1>
      <ThesisReport thesis={session.final_thesis ?? ""} />
      <h2>Performance Metrics (Top Picks)</h2>
      <MetricsTable metrics={metrics} />
      <PerformanceChart series={priceHistory ?? {}} names={names} />
      <RiskReturnScatter metrics={metrics} />
    </div>
  );
}
