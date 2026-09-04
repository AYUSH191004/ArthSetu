import { useQuery } from "@tanstack/react-query";
import { Menu } from "lucide-react";
import { healthApi } from "@/api/endpoints";
import { GlobalSearch } from "@/components/GlobalSearch";
import { cn } from "@/lib/cn";

export function Topbar({ onMenuClick }: { onMenuClick: () => void }) {
  const { data, isError } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.get,
    refetchInterval: 30_000,
  });

  const online = !isError && data?.status === "ok";

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-line bg-surface px-4 sm:px-5">
      <button
        onClick={onMenuClick}
        className="rounded p-1.5 text-ink-muted hover:bg-surface-muted hover:text-ink lg:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      <GlobalSearch />

      <div className="ml-auto flex items-center gap-3 text-[12px]">
        {data?.environment && (
          <span className="hidden rounded-md bg-surface-muted px-2 py-1 font-medium capitalize text-ink-muted sm:inline">
            {data.environment}
          </span>
        )}
        <span className="flex items-center gap-1.5 text-ink-muted">
          <span
            className={cn("h-2 w-2 rounded-full", online ? "bg-ok" : "bg-danger")}
            aria-hidden
          />
          <span className="hidden sm:inline">
            {online ? "API online" : "API offline"}
          </span>
        </span>
      </div>
    </header>
  );
}
