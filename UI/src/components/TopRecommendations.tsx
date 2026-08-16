import type { AssetMetrics } from "../lib/apiClient";
import { groupByInstrumentType } from "../lib/groupByCategory";

interface TopRecommendationsProps {
  metrics: AssetMetrics[];
}

const TOP_N = 3;

const ACCENTS = [
  { text: "text-primary", border: "border-primary/20", chip: "text-primary" },
  { text: "text-secondary", border: "border-secondary/20", chip: "text-secondary" },
  { text: "text-tertiary", border: "border-tertiary/20", chip: "text-tertiary" },
] as const;

const CATEGORY_ICONS: Record<string, string> = {
  Stocks: "candlestick_chart",
  "Mutual Funds/ETFs": "pie_chart",
  "Gold/Commodities": "diamond",
};

function categoryLabel(category: string): string {
  return `Top ${category}`;
}

export function TopRecommendations({ metrics }: TopRecommendationsProps) {
  const groups = groupByInstrumentType(metrics);
  if (groups.size === 0) return null;

  return (
    <div>
      <h3 className="text-lg font-headline font-semibold text-on-surface mt-8 mb-4">
        Top Recommendations
      </h3>
      <div
        className="grid grid-cols-1 gap-4"
        style={{ gridTemplateColumns: `repeat(${groups.size}, minmax(0, 1fr))` }}
      >
        {Array.from(groups.entries()).map(([category, group], i) => {
          const accent = ACCENTS[i % ACCENTS.length];
          const top3 = [...group].sort((a, b) => b.sharpe_ratio - a.sharpe_ratio).slice(0, TOP_N);
          return (
            <div className="space-y-3" key={category}>
              <h4
                className={`text-sm font-headline font-bold uppercase tracking-wider mb-2 flex items-center gap-2 ${accent.text}`}
              >
                <span className="material-symbols-outlined text-sm">
                  {CATEGORY_ICONS[category] ?? "insights"}
                </span>
                {categoryLabel(category)}
              </h4>
              {top3.map((m, rank) => (
                <div
                  key={m.ticker}
                  className={`bg-surface-container-low/50 p-4 rounded-lg border backdrop-blur-sm ${accent.border}`}
                >
                  <h5 className="font-bold text-on-surface flex items-baseline gap-2">
                    <span className={`font-mono text-lg ${accent.chip}`}>{rank + 1}.</span>
                    {m.name}
                  </h5>
                  <p className="text-xs text-on-surface-variant mt-1">
                    Sharpe {m.sharpe_ratio.toFixed(2)} · {m.trend} trend ·{" "}
                    {m.return_1y_pct.toFixed(1)}% 1Y return
                  </p>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
