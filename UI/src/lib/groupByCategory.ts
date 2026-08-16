import type { AssetMetrics } from "./apiClient";

const FALLBACK_CATEGORY = "Other";

/** Groups metrics by instrument_type, in first-seen order. Falls back to
 * "Other" for sessions checkpointed before this field existed (either
 * missing from the payload, or an old checkpoint deserializing without it
 * entirely). */
export function groupByInstrumentType(metrics: AssetMetrics[]): Map<string, AssetMetrics[]> {
  const groups = new Map<string, AssetMetrics[]>();
  for (const m of metrics) {
    const category = m.instrument_type ?? FALLBACK_CATEGORY;
    const group = groups.get(category);
    if (group) {
      group.push(m);
    } else {
      groups.set(category, [m]);
    }
  }
  return groups;
}
