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
        <div className="bg-background text-foreground flex min-h-screen flex-col items-center justify-center p-4">
          <div className="border-surface-border bg-surface w-full max-w-lg rounded-3xl border p-10 shadow-2xl">
            <h2 className="text-destructive mb-4 text-2xl font-bold tracking-tight uppercase">
              Something went wrong.
            </h2>
            <p className="text-text-muted mb-6 font-medium">
              An unexpected error occurred. Please try refreshing the page.
            </p>
            {this.state.error && (
              <details className="border-surface-border bg-background/50 text-mini text-destructive/80 mb-8 max-h-48 overflow-auto rounded-2xl border p-4 font-mono whitespace-pre-wrap">
                <summary className="mb-2 cursor-pointer font-bold tracking-[0.2em] uppercase opacity-60">
                  Error Details
                </summary>
                {this.state.error.toString()}
              </details>
            )}
            <Button onClick={() => window.location.reload()} className="h-12 w-full">
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
