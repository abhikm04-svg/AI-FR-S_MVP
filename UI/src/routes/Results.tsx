import { useParams } from "react-router-dom";
import { MetricsTable } from "../components/MetricsTable";
import { PerformanceChart } from "../components/PerformanceChart";
import { RiskReturnScatter } from "../components/RiskReturnScatter";
import { ThesisReport } from "../components/ThesisReport";
import { TopRecommendations } from "../components/TopRecommendations";
import { usePriceHistory, useSessionDetail } from "../hooks/useSessions";
import { groupByInstrumentType } from "../lib/groupByCategory";

const AGENT_SEALS = [
  { name: "Chanakya", role: "Market Researcher", icon: "travel_explore", color: "var(--color-primary)" },
  { name: "Aryabhata", role: "Financial Analyst", icon: "calculate", color: "var(--color-secondary)" },
  { name: "Tagore", role: "Business Analyst", icon: "description", color: "var(--color-tertiary)" },
] as const;

function relativeTime(isoDate: string): string {
  const diffMs = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function Results() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data: session, isLoading } = useSessionDetail(sessionId);
  const { data: priceHistory } = usePriceHistory(sessionId);

  if (isLoading || !session) {
    return <p>Loading results…</p>;
  }

  const metrics = session.analyzed_metrics ?? [];
  const names = Object.fromEntries(metrics.map((m) => [m.ticker, m.name]));
  const groups = groupByInstrumentType(metrics);

  return (
    <div>
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-secondary-container/50 text-on-secondary-container text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wider border border-secondary/20">
              Analysis Complete
            </span>
            <span className="text-on-surface-variant text-sm">
              Generated {relativeTime(session.created_at)}
            </span>
          </div>
          <h1 className="text-3xl font-headline font-semibold text-on-surface tracking-tight">
            Final Investment Report
          </h1>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            disabled
            title="Not yet supported"
            className="flex items-center gap-2 bg-surface-container-high/50 border border-outline-variant/30 text-on-surface px-4 py-2 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-sm">share</span>
            Share
          </button>
          <button
            type="button"
            disabled
            title="Not yet supported"
            className="flex items-center gap-2 bg-primary/10 border border-primary/30 text-primary px-4 py-2 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed"
          >
            <span className="material-symbols-outlined text-sm">download</span>
            Export PDF
          </button>
        </div>
      </div>

      <article className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 p-8">
        <h2 className="text-2xl font-headline font-semibold text-primary mb-6 flex items-center gap-2 border-b border-outline-variant/30 pb-4">
          <span className="material-symbols-outlined">psychology</span>
          AI Investment Thesis
        </h2>
        <ThesisReport thesis={session.final_thesis ?? ""} />
        <div className="flex items-center gap-5 mt-8 pt-5 border-t border-outline-variant/20">
          <span className="text-xs text-on-surface-variant uppercase tracking-wider">Sealed by</span>
          {AGENT_SEALS.map((agent) => (
            <div key={agent.name} className="flex items-center gap-2" title={agent.role}>
              <span
                className="agent-seal w-7 h-7 text-[0.7rem]"
                style={{ ["--seal" as string]: agent.color }}
                aria-hidden="true"
              >
                <span className="material-symbols-outlined text-sm">{agent.icon}</span>
              </span>
              <span className="text-xs text-on-surface-variant">{agent.name}</span>
            </div>
          ))}
        </div>
      </article>

      <div className="mt-8">
        <TopRecommendations metrics={metrics} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <PerformanceChart series={priceHistory ?? {}} names={names} />
        <RiskReturnScatter metrics={metrics} />
      </div>

      <div className="mt-8 space-y-8">
        {Array.from(groups.entries()).map(([category, group]) => (
          <section
            key={category}
            className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 overflow-hidden"
          >
            <div className="p-6 border-b border-outline-variant/30 bg-surface-container-low/30">
              <h3 className="font-headline font-semibold text-on-surface">{category}</h3>
              <p className="text-xs text-on-surface-variant">Top selected {group.length}</p>
            </div>
            <MetricsTable metrics={group} />
          </section>
        ))}
      </div>
    </div>
  );
}
