/**
 * Chart color tokens from the dataviz skill's reference palette
 * (references/palette.md), used as-is/unmodified -- no re-validation
 * needed since the documented ΔE results already cover exactly how these
 * are used here:
 *
 * - PerformanceChart (line, up to 5 series/assets): uses categorical slots
 *   1-5 in fixed order. Palette.md documents the full 8-slot order as
 *   adjacent-pair-validated for line charts.
 * - RiskReturnScatter (bubble, colored by Trend: 2 categories): uses only
 *   slots 1-2, well within the "first three slots validate all-pairs"
 *   scatter/bubble cap.
 *
 * Recharts renders SVG presentation attributes directly (not through a
 * stylesheet), so plain resolved hex is used here rather than CSS custom
 * properties -- dark mode is a deliberate lookup against its own validated
 * steps (see palette.md), not an automatic var() flip.
 */

export const CATEGORICAL_LIGHT = [
  "#2a78d6", // slot 1 blue
  "#eb6834", // slot 2 orange
  "#1baf7a", // slot 3 aqua
  "#eda100", // slot 4 yellow
  "#e87ba4", // slot 5 magenta
] as const;

export const CATEGORICAL_DARK = [
  "#3987e5",
  "#d95926",
  "#199e70",
  "#c98500",
  "#d55181",
] as const;

export const CHART_INK = {
  light: { primary: "#0b0b0b", secondary: "#52514e", muted: "#898781", grid: "#e1e0d9" },
  dark: { primary: "#ffffff", secondary: "#c3c2b7", muted: "#898781", grid: "#2c2c2a" },
} as const;

export function usePrefersDark(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function categoricalColors(isDark: boolean): readonly string[] {
  return isDark ? CATEGORICAL_DARK : CATEGORICAL_LIGHT;
}

export function chartInk(isDark: boolean) {
  return isDark ? CHART_INK.dark : CHART_INK.light;
}
