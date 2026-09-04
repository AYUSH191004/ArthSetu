import { useState, type FormEvent } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { Network } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import type { ApiError } from "@/lib/api";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Field";

export function LoginPage() {
  useDocumentTitle("Sign in");
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/dashboard";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && user) return <Navigate to={next} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username.trim(), password);
      navigate(next, { replace: true });
    } catch (err) {
      setError((err as ApiError)?.message ?? "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-brand text-white">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <div className="text-base font-semibold text-ink">ArthSetu</div>
            <div className="text-[12px] text-ink-subtle">
              Business Intelligence Console
            </div>
          </div>
        </div>

        <form
          onSubmit={submit}
          className="space-y-4 rounded-lg border border-line bg-surface p-5 shadow-card"
        >
          <div>
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              required
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          {error && (
            <p className="rounded-md bg-danger/10 px-3 py-2 text-[13px] text-danger">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" loading={busy}>
            Sign in
          </Button>
        </form>

        <p className="mt-4 text-center text-[12px] text-ink-subtle">
          Demo: <span className="font-mono">admin / arthsetu-admin</span> ·{" "}
          <span className="font-mono">reviewer / arthsetu-review</span> ·{" "}
          <span className="font-mono">officer / arthsetu-view</span>
        </p>
      </div>
    </div>
  );
}
