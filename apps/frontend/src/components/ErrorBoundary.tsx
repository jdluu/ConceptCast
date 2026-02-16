import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[var(--background)] text-[var(--foreground)] p-4">
          <div className="bg-[var(--surface)] border border-[var(--surface-border)] p-8 rounded-2xl shadow-2xl max-w-lg w-full">
            <h2 className="text-2xl font-bold mb-4 text-red-500">Something went wrong.</h2>
            <p className="mb-4 text-[var(--text-muted)] font-medium">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="mb-6 p-4 bg-[var(--background)] border border-[var(--surface-border)] rounded-xl text-xs overflow-auto max-h-48 whitespace-pre-wrap font-mono text-red-500/80">
                <summary className="cursor-pointer mb-2 font-bold uppercase tracking-widest opacity-60">Error Details</summary>
                {this.state.error.toString()}
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition-colors"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
