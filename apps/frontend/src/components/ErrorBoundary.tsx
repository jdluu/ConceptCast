import { Component, ErrorInfo, ReactNode } from 'react';

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
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--background)] p-4 text-[var(--foreground)]">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] p-8 shadow-2xl">
            <h2 className="mb-4 text-2xl font-bold text-red-500">Something went wrong.</h2>
            <p className="mb-4 font-medium text-[var(--text-muted)]">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="mb-6 max-h-48 overflow-auto rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-4 font-mono text-xs whitespace-pre-wrap text-red-500/80">
                <summary className="mb-2 cursor-pointer font-bold tracking-widest uppercase opacity-60">
                  Error Details
                </summary>
                {this.state.error.toString()}
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="w-full rounded bg-red-600 px-4 py-2 font-bold text-white transition-colors hover:bg-red-700"
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
