import { Activity } from 'lucide-react';

interface FailedJobViewProps {
  errorMessage: string | null;
}

/**
 * Displays a full-page error state with a retry button when a job has failed.
 */
export function FailedJobView({ errorMessage }: FailedJobViewProps) {
  return (
    <div className="min-h-md flex flex-col items-center justify-center p-8 text-center">
      <div className="border-destructive/20 bg-destructive/10 text-destructive mb-6 flex h-16 w-16 items-center justify-center rounded-full border">
        <Activity className="h-8 w-8" />
      </div>
      <h2 className="text-foreground mb-2 text-2xl font-bold">Generation Halted</h2>
      <p className="text-text-muted mb-8 max-w-md">
        {errorMessage || 'The council encountered an unexpected synchronization error.'}
      </p>
      <button
        onClick={() => window.location.reload()}
        className="bg-foreground text-background rounded-xl px-8 py-3 font-bold transition-opacity hover:opacity-90"
      >
        Retry Connection
      </button>
    </div>
  );
}
