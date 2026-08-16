import type { AssetMetrics } from "../lib/apiClient";

interface MetricsTableProps {
  metrics: AssetMetrics[];
}

export function MetricsTable({ metrics }: MetricsTableProps) {
  if (metrics.length === 0) {
    return <p>No metrics available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-container/20 text-xs text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/30">
            <th className="py-3 px-6 font-semibold">Name</th>
            <th className="py-3 px-6 font-semibold text-right">Price (₹)</th>
            <th className="py-3 px-6 font-semibold text-right">1Y Return</th>
            <th className="py-3 px-6 font-semibold text-right">Volatility</th>
            <th className="py-3 px-6 font-semibold text-right">Sharpe</th>
            <th className="py-3 px-6 font-semibold text-center">Trend</th>
            <th className="py-3 px-6 font-semibold text-right">P/E</th>
            <th className="py-3 px-6 font-semibold text-right">ROE</th>
          </tr>
        </thead>
        <tbody className="text-sm text-on-surface divide-y divide-outline-variant/20">
          {metrics.map((m) => (
            <tr key={m.ticker} className="hover:bg-surface-container-low/50 transition-colors">
              <td className="py-3 px-6 font-medium">{m.name}</td>
              <td className="py-3 px-6 text-right font-mono text-xs text-on-surface-variant">
                ₹{m.last_price_inr.toFixed(2)}
              </td>
              <td
                className={`py-3 px-6 text-right font-mono text-xs font-medium ${m.return_1y_pct >= 0 ? "text-success" : "text-error"}`}
              >
                {m.return_1y_pct.toFixed(2)}%
              </td>
              <td className="py-3 px-6 text-right font-mono text-xs text-on-surface-variant">
                {m.volatility_pct.toFixed(2)}%
              </td>
              <td className="py-3 px-6 text-right font-mono text-xs text-on-surface-variant">
                {m.sharpe_ratio.toFixed(2)}
              </td>
              <td className="py-3 px-6 text-center">
                <span
                  className={`material-symbols-outlined text-sm ${m.trend === "Bullish" ? "text-success" : "text-error"}`}
                >
                  {m.trend === "Bullish" ? "trending_up" : "trending_down"}
                </span>
              </td>
              <td className="py-3 px-6 text-right font-mono text-xs text-on-surface-variant">{m.pe_ratio}</td>
              <td className="py-3 px-6 text-right font-mono text-xs text-on-surface-variant">{m.roe}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
