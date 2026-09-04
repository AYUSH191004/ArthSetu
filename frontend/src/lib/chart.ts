import type { EntityStatus } from "./format";

// Hex mirrors of the --chart-* CSS variables in index.css.
// Recharts needs concrete color strings, not Tailwind classes.
export const CHART = {
  series: "#1e4fd8",
  grid: "#e2e8f0",
  axis: "#898781",
  surface: "#ffffff",
} as const;

export const STATUS_COLOR: Record<EntityStatus, string> = {
  active: "#15803d",
  dormant: "#ca8a04",
  closed: "#b91c1c",
  unknown: "#64748b",
};

// Fixed display order for status part-to-whole marks.
export const STATUS_ORDER: EntityStatus[] = [
  "active",
  "dormant",
  "closed",
  "unknown",
];

/** "2026-07" -> "Jul '26" */
export function shortMonth(ym: string): string {
  const [y, m] = ym.split("-").map(Number);
  if (!y || !m) return ym;
  const d = new Date(y, m - 1, 1);
  return `${d.toLocaleString("en", { month: "short" })} '${String(y).slice(2)}`;
}
