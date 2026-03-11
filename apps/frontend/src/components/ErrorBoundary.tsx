import { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/Common';

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
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-foreground">
          <div className="w-full max-w-lg rounded-3xl border border-surface-border bg-surface p-10 shadow-2xl">
            <h2 className="mb-4 text-2xl font-bold text-destructive uppercase tracking-tight">Something went wrong.</h2>
            <p className="mb-6 font-medium text-text-muted">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="mb-8 max-h-48 overflow-auto rounded-2xl border border-surface-border bg-background/50 p-4 font-mono text-mini whitespace-pre-wrap text-destructive/80">
                <summary className="mb-2 cursor-pointer font-bold tracking-[0.2em] uppercase opacity-60">
                  Error Details
                </summary>
                {this.state.error.toString()}
              </details>
            )}
            <Button
              onClick={() => window.location.reload()}
              className="w-full h-12"
            >
              Refresh Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
