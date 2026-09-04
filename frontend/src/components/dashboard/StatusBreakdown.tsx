import { Link } from "react-router-dom";
import { STATUS_COLOR, STATUS_ORDER } from "@/lib/chart";
import { statusMeta, formatNumber, type EntityStatus } from "@/lib/format";
import { cn } from "@/lib/cn";

interface Props {
  counts: Record<EntityStatus, number>;
}

export function StatusBreakdown({ counts }: Props) {
  const total = STATUS_ORDER.reduce((s, k) => s + (counts[k] || 0), 0);
  const segments = STATUS_ORDER.map((key) => ({
    key,
    label: statusMeta(key).label,
    value: counts[key] || 0,
    pct: total ? (counts[key] || 0) / total : 0,
  })).filter((s) => s.value > 0);

  return (
    <div>
      {/* segmented part-to-whole bar; 2px surface gaps between fills */}
      <div className="flex h-7 w-full gap-[2px] overflow-hidden rounded-md">
        {segments.map((s) => (
          <div
            key={s.key}
            className="group relative flex items-center justify-center"
            style={{ width: `${Math.max(s.pct * 100, 4)}%`, background: STATUS_COLOR[s.key] }}
            title={`${s.label}: ${formatNumber(s.value)} (${(s.pct * 100).toFixed(0)}%)`}
          >
            {s.pct > 0.08 && (
              <span className="text-[11px] font-semibold text-white tabular-nums">
                {(s.pct * 100).toFixed(0)}%
              </span>
            )}
          </div>
        ))}
      </div>

      {/* legend — the dependable identity channel */}
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2">
        {STATUS_ORDER.map((key) => {
          const value = counts[key] || 0;
          const pct = total ? (value / total) * 100 : 0;
          return (
            <li key={key}>
              <Link
                to={`/businesses?status=${key}`}
                className={cn(
                  "flex items-center gap-2 rounded-md px-1.5 py-1 text-[13px] transition-colors hover:bg-surface-muted",
                  value === 0 && "opacity-55",
                )}
              >
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-[3px]"
                  style={{ background: STATUS_COLOR[key] }}
                  aria-hidden
                />
                <span className="text-ink-muted">{statusMeta(key).label}</span>
                <span className="ml-auto font-semibold tabular-nums text-ink">
                  {formatNumber(value)}
                </span>
                <span className="w-9 text-right tabular-nums text-ink-subtle">
                  {pct.toFixed(0)}%
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
