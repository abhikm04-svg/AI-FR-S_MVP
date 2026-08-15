import type { AssetMetrics } from "../lib/apiClient";

interface MetricsTableProps {
  metrics: AssetMetrics[];
}

export function MetricsTable({ metrics }: MetricsTableProps) {
  if (metrics.length === 0) {
    return <p>No metrics available.</p>;
  }

  return (
    <div className="card" style={{ overflowX: "auto" }}>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Price (₹)</th>
            <th>1Y Return</th>
            <th>Volatility</th>
            <th>Sharpe</th>
            <th>Trend</th>
            <th>P/E</th>
            <th>ROE</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((m) => (
            <tr key={m.ticker}>
              <td>{m.name}</td>
              <td>₹{m.last_price_inr.toFixed(2)}</td>
              <td>{m.return_1y_pct.toFixed(2)}%</td>
              <td>{m.volatility_pct.toFixed(2)}%</td>
              <td>{m.sharpe_ratio.toFixed(2)}</td>
              <td>{m.trend}</td>
              <td>{m.pe_ratio}</td>
              <td>{m.roe}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
