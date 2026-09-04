import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  ClipboardCheck,
  Map,
  Network,
  Users,
  X,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import type { Role } from "@/types/api";
import { cn } from "@/lib/cn";

const nav: {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
  role?: Role;
}[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/businesses", label: "Business Search", icon: Search },
  { to: "/reviews", label: "Review Queue", icon: ClipboardCheck },
  { to: "/districts", label: "District Analytics", icon: Map },
  { to: "/users", label: "Users", icon: Users, role: "admin" },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { can } = useAuth();
  const items = nav.filter((n) => !n.role || can(n.role));

  return (
    <>
      {/* backdrop (mobile only) */}
      <div
        className={cn(
          "fixed inset-0 z-30 bg-ink/30 transition-opacity lg:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={onClose}
        aria-hidden
      />

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 shrink-0 flex-col border-r border-line bg-surface transition-transform",
          "lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center gap-2 border-b border-line px-4">
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-white">
            <Network className="h-4 w-4" />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-semibold text-ink">ArthSetu</div>
            <div className="text-[11px] text-ink-subtle">BI Console</div>
          </div>
          <button
            onClick={onClose}
            className="ml-auto rounded p-1 text-ink-subtle hover:text-ink lg:hidden"
            aria-label="Close menu"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 p-2">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium transition-colors",
                  isActive
                    ? "bg-brand-soft text-brand"
                    : "text-ink-muted hover:bg-surface-muted hover:text-ink",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-line px-4 py-3 text-[11px] text-ink-subtle">
          Unified Business Identity &amp; Activity Intelligence
        </div>
      </aside>
    </>
  );
}
