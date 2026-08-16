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
import { categoricalColors, chartInk } from "../lib/theme";

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
  // App is dark-only (Glacier theme, no light variant) -- hardcode dark chart
  // colors rather than following the OS-level prefers-color-scheme, which
  // would otherwise mismatch the app's fixed-dark chrome on a light-mode OS.
  const colors = categoricalColors(true);
  const ink = chartInk(true);

  const tickers = Object.keys(series);
  const rows = useMemo(() => buildChartRows(series), [series]);

  if (tickers.length === 0) {
    return <p>No price history available for the top picks yet.</p>;
  }

  return (
    <div className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 p-6 flex flex-col">
      <h3 className="font-headline font-semibold text-on-surface mb-1">
        Comparative Performance (Normalized)
      </h3>
      <p style={{ color: ink.secondary, fontSize: "0.9em" }} className="mb-4">
        Growth of ₹100 invested at the start of the period.
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke={ink.grid} vertical={false} />
          <XAxis dataKey="date" stroke={ink.muted} tick={{ fontSize: 12 }} minTickGap={32} />
          <YAxis stroke={ink.muted} tick={{ fontSize: 12 }} width={48} />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface-container-high)",
              border: "1px solid var(--color-outline-variant)",
              borderRadius: "var(--radius-DEFAULT)",
            }}
          />
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
