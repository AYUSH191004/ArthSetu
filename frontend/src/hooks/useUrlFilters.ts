import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * Generic URL-query-param state. `keys` lists the params this view owns;
 * anything not in the list is left untouched. Setting any "filter" key
 * resets `offset` to 0.
 */
export function useUrlFilters<K extends string>(keys: readonly K[]) {
  const [params, setParams] = useSearchParams();

  const values = useMemo(() => {
    const out = {} as Record<K | "offset", string>;
    for (const k of keys) out[k] = params.get(k) ?? "";
    out.offset = params.get("offset") ?? "0";
    return out;
  }, [params, keys]);

  const setFilter = useCallback(
    (patch: Partial<Record<K, string>>) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          for (const [k, v] of Object.entries(patch)) {
            if (v) next.set(k, v as string);
            else next.delete(k);
          }
          next.delete("offset");
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const setOffset = useCallback(
    (offset: number) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (offset > 0) next.set("offset", String(offset));
          else next.delete("offset");
          return next;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const clear = useCallback(() => setParams({}, { replace: true }), [setParams]);

  return { values, offset: Number(values.offset) || 0, setFilter, setOffset, clear };
}
