import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { statusMeta } from "@/lib/format";

type Tone = "ok" | "warn" | "danger" | "neutral" | "brand";

const tones: Record<Tone, string> = {
  ok: "bg-ok/10 text-ok ring-ok/20",
  warn: "bg-warn/10 text-warn ring-warn/20",
  danger: "bg-danger/10 text-danger ring-danger/20",
  neutral: "bg-surface-muted text-ink-muted ring-line",
  brand: "bg-brand-soft text-brand ring-brand/20",
};

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const meta = statusMeta(status);
  return (
    <Badge tone={meta.tone}>
      <span
        className={cn("h-1.5 w-1.5 rounded-full", {
          "bg-ok": meta.tone === "ok",
          "bg-warn": meta.tone === "warn",
          "bg-danger": meta.tone === "danger",
          "bg-ink-subtle": meta.tone === "neutral",
        })}
        aria-hidden
      />
      {meta.label}
    </Badge>
  );
}
