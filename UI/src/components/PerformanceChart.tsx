import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "../lib/apiClient";
import { categoricalColors, chartInk, usePrefersDark } from "../lib/theme";

interface PerformanceChartProps {
  series: Record<string, PricePoint[]>;
  names?: Record<string, string>;
}

interface ChartRow {
  date: string;
  [ticker: string]: string | number;
}

/** Pure data-shaping: {ticker: PricePoint[]} -> one row per date, columns
 * per ticker -- the shape Recharts' LineChart wants. Exported for testing
 * without needing to render. */
export function buildChartRows(series: Record<string, PricePoint[]>): ChartRow[] {
  const dateSet = new Set<string>();
  for (const points of Object.values(series)) {
    for (const p of points) dateSet.add(p.date);
  }
  const dates = Array.from(dateSet).sort();

  const lookups = Object.fromEntries(
    Object.entries(series).map(([ticker, points]) => [
      ticker,
      new Map(points.map((p) => [p.date, p.value])),
    ]),
  );

  return dates.map((date) => {
    const row: ChartRow = { date };
    for (const [ticker, lookup] of Object.entries(lookups)) {
      const value = lookup.get(date);
      if (value !== undefined) row[ticker] = value;
    }
    return row;
  });
}

export function PerformanceChart({ series, names = {} }: PerformanceChartProps) {
  const isDark = usePrefersDark();
  const colors = categoricalColors(isDark);
  const ink = chartInk(isDark);

  const tickers = Object.keys(series);
  const rows = useMemo(() => buildChartRows(series), [series]);

  if (tickers.length === 0) {
    return <p>No price history available for the top picks yet.</p>;
  }

  return (
    <div className="card">
      <h3>Comparative Performance (Normalized)</h3>
      <p style={{ color: ink.secondary, fontSize: "0.9em" }}>
        Growth of ₹100 invested at the start of the period.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={ink.grid} vertical={false} />
          <XAxis dataKey="date" stroke={ink.muted} tick={{ fontSize: 12 }} minTickGap={32} />
          <YAxis stroke={ink.muted} tick={{ fontSize: 12 }} width={48} />
          <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)" }} />
          <Legend
            formatter={(value: string) => (
              <span style={{ color: ink.secondary }}>{names[value] ?? value}</span>
            )}
          />
          {tickers.map((ticker, i) => (
            <Line
              key={ticker}
              type="monotone"
              dataKey={ticker}
              name={ticker}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
