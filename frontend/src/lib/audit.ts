import {
  ArrowLeftRight,
  CheckCircle2,
  CircleSlash,
  FileEdit,
  GitMerge,
  PlusCircle,
  RefreshCw,
  type LucideIcon,
} from "lucide-react";
import type { AuditEntry } from "@/types/api";
import { titleCase } from "./format";

interface AuditView {
  icon: LucideIcon;
  tone: "ok" | "warn" | "danger" | "brand" | "neutral";
  title: string;
  detail?: string;
}

function stateStr(state: unknown, key: string): string | undefined {
  if (state && typeof state === "object" && key in state) {
    const v = (state as Record<string, unknown>)[key];
    return v == null ? undefined : String(v);
  }
  return undefined;
}

export function describeAudit(entry: AuditEntry): AuditView {
  const action = entry.action ?? "";
  const after = entry.after_state;

  switch (action) {
    case "STATUS_UPDATED":
    case "STATUS_INFERRED": {
      const status = stateStr(after, "status");
      const conf = stateStr(after, "confidence");
      return {
        icon: RefreshCw,
        tone: "brand",
        title: status ? `Status set to ${titleCase(status)}` : "Status recomputed",
        detail: conf ? `confidence ${Number(conf).toFixed(2)}` : undefined,
      };
    }
    case "REVIEW_APPROVED":
      return {
        icon: CheckCircle2,
        tone: "ok",
        title: "Review approved",
        detail: stateStr(after, "link_id") ? "link confirmed" : undefined,
      };
    case "REVIEW_REJECTED":
      return { icon: CircleSlash, tone: "danger", title: "Review rejected" };
    case "REVIEW_CREATED":
      return { icon: ArrowLeftRight, tone: "warn", title: "Sent to review queue" };
    case "AUTO_LINK":
    case "AUTO_LINK_EVALUATED": {
      const conf = stateStr(after, "confidence");
      const decision = stateStr(after, "decision");
      return {
        icon: GitMerge,
        tone: "neutral",
        title: decision ? `Link ${titleCase(decision)}` : "Record auto-linked",
        detail: conf ? `confidence ${Number(conf).toFixed(2)}` : undefined,
      };
    }
    case "NEW_ENTITY_CREATED":
      return {
        icon: PlusCircle,
        tone: "brand",
        title: "New business identity created",
        detail: stateStr(after, "ubid_code"),
      };
    case "DATA_CORRECTION":
      return { icon: FileEdit, tone: "neutral", title: "Manual data correction" };
    default:
      return { icon: FileEdit, tone: "neutral", title: titleCase(action || "Event") };
  }
}
