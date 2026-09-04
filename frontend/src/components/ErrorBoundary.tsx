import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "./ui/Button";

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Render error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
          <h1 className="text-lg font-semibold text-ink">
            The console hit an unexpected error
          </h1>
          <p className="max-w-md text-[13px] text-ink-muted">
            {this.state.error.message}
          </p>
          <Button onClick={() => window.location.reload()}>Reload console</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
