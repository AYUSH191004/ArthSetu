import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-center">
      <p className="text-3xl font-semibold text-ink">404</p>
      <p className="text-[13px] text-ink-muted">
        That page isn&apos;t part of the console.
      </p>
      <Link to="/">
        <Button variant="secondary" size="sm">
          Back to dashboard
        </Button>
      </Link>
    </div>
  );
}
