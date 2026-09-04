import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export function Table({ className, ...props }: HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="w-full overflow-x-auto">
      <table
        className={cn("w-full border-collapse text-sm", className)}
        {...props}
      />
    </div>
  );
}

export function Th({ className, ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      scope="col"
      className={cn(
        "border-b border-line bg-surface-muted px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-ink-muted",
        className,
      )}
      {...props}
    />
  );
}

export function Td({ className, ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn("border-b border-line px-3 py-2.5 align-middle text-ink", className)}
      {...props}
    />
  );
}

export function Tr({
  className,
  interactive,
  onClick,
  ...props
}: HTMLAttributes<HTMLTableRowElement> & { interactive?: boolean }) {
  return (
    <tr
      onClick={onClick}
      onKeyDown={
        interactive && onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                e.currentTarget.click();
              }
            }
          : undefined
      }
      tabIndex={interactive && onClick ? 0 : undefined}
      className={cn(
        interactive &&
          "cursor-pointer transition-colors hover:bg-brand-soft/60 focus-visible:bg-brand-soft/60",
        className,
      )}
      {...props}
    />
  );
}
