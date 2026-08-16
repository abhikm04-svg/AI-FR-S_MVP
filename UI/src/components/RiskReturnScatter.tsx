import {
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { AssetMetrics } from "../lib/apiClient";
import { categoricalColors, chartInk } from "../lib/theme";

interface RiskReturnScatterProps {
  metrics: AssetMetrics[];
}

type BubblePoint = AssetMetrics & { sharpe: number };

const TREND_ORDER = ["Bullish", "Bearish"] as const;

/** Sharpe ratio drives bubble size -- must be positive for Recharts'
 * Z-axis range mapping, so a negative/zero Sharpe still renders a
 * (small) visible bubble rather than vanishing. */
export function bubbleSize(m: AssetMetrics): number {
  return Math.max(m.sharpe_ratio, 0.01);
}

interface ScatterTooltipProps {
  active?: boolean;
  payload?: Array<{ payload: BubblePoint }>;
}

function ScatterTooltip({ active, payload }: ScatterTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className="bg-surface-container rounded-lg border border-outline-variant/30 p-2.5 text-sm text-on-surface">
      <strong>{point.name}</strong>
      <div>Volatility: {point.volatility_pct}%</div>
      <div>Return: {point.return_1y_pct}%</div>
      <div>Sharpe: {point.sharpe_ratio}</div>
      <div>P/E: {point.pe_ratio}</div>
      <div>ROE: {point.roe}</div>
    </div>
  );
}

export function RiskReturnScatter({ metrics }: RiskReturnScatterProps) {
  // See PerformanceChart.tsx -- app is dark-only, chart colors hardcoded to
  // the dark variant rather than following the OS light/dark setting.
  const colors = categoricalColors(true);
  const ink = chartInk(true);

  if (metrics.length === 0) {
    return <p>No assets to plot.</p>;
  }

  return (
    <div className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 p-6 flex flex-col">
      <h3 className="font-headline font-semibold text-on-surface mb-1">Risk vs Reward Landscape</h3>
      <p style={{ color: ink.secondary, fontSize: "0.9em" }} className="mb-4">
        Larger bubble = better risk-adjusted return (Sharpe ratio).
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid stroke={ink.grid} />
          <XAxis
            type="number"
            dataKey="volatility_pct"
            name="Volatility"
            unit="%"
            stroke={ink.muted}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            type="number"
            dataKey="return_1y_pct"
            name="1Y Return"
            unit="%"
            stroke={ink.muted}
            tick={{ fontSize: 12 }}
          />
          <ZAxis type="number" dataKey="sharpe" range={[64, 400]} />
          <Tooltip cursor={{ strokeDasharray: "3 3" }} content={<ScatterTooltip />} />
          <Legend />
          {TREND_ORDER.map((trend, i) => (
            <Scatter
              key={trend}
              name={trend}
              data={metrics
                .filter((m) => m.trend === trend)
                .map((m): BubblePoint => ({ ...m, sharpe: bubbleSize(m) }))}
              fill={colors[i % colors.length]}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
