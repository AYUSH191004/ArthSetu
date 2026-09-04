import { useNavigate } from "react-router-dom";
import type { DistrictRow } from "@/types/api";
import { STATUS_COLOR, STATUS_ORDER } from "@/lib/chart";
import { statusMeta, formatNumber } from "@/lib/format";

/**
 * Horizontal stacked bars — one row per district. Bar length encodes the
 * district total; segments encode the status mix (2px surface gaps).
 * Clicking a segment drills into the filtered business search.
 */
export function DistrictBars({ rows }: { rows: DistrictRow[] }) {
  const navigate = useNavigate();
  const sorted = [...rows].sort((a, b) => b.total - a.total);
  const max = sorted[0]?.total ?? 1;

  return (
    <div className="space-y-3">
      {sorted.map((d) => (
        <div
          key={d.district}
          className="grid grid-cols-[5.5rem_1fr_2rem] items-center gap-2 sm:grid-cols-[8rem_1fr_2.5rem] sm:gap-3"
        >
          <button
            onClick={() =>
              navigate(`/businesses?district=${encodeURIComponent(d.district)}`)
            }
            className="truncate text-right text-[12px] font-medium text-ink hover:text-brand hover:underline sm:text-[13px]"
            title={d.district}
          >
            {d.district}
          </button>

          <div
            className="flex h-5 gap-[2px] overflow-hidden rounded"
            style={{ width: `${Math.max((d.total / max) * 100, 4)}%` }}
          >
            {STATUS_ORDER.map((key) => {
              const value = d[key];
              if (!value) return null;
              const label = statusMeta(key).label;
              return (
                <button
                  key={key}
                  onClick={() =>
                    navigate(
                      `/businesses?district=${encodeURIComponent(d.district)}&status=${key}`,
                    )
                  }
                  className="h-full min-w-0 transition-opacity hover:opacity-80"
                  style={{
                    flex: `${value} 1 0`,
                    background: STATUS_COLOR[key],
                  }}
                  title={`${d.district} · ${label}: ${formatNumber(value)}`}
                  aria-label={`${d.district}, ${label}: ${value}`}
                />
              );
            })}
          </div>

          <span className="text-[12px] tabular-nums text-ink-muted sm:text-[13px]">
            {formatNumber(d.total)}
          </span>
        </div>
      ))}

      <div className="flex flex-wrap gap-x-4 gap-y-1 pt-1">
        {STATUS_ORDER.map((key) => (
          <span
            key={key}
            className="flex items-center gap-1.5 text-[12px] text-ink-muted"
          >
            <span
              className="h-2.5 w-2.5 rounded-[3px]"
              style={{ background: STATUS_COLOR[key] }}
              aria-hidden
            />
            {statusMeta(key).label}
          </span>
        ))}
      </div>
    </div>
  );
}
