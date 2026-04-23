import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { AlertTriangle } from 'lucide-react';
import { GeneratingLessonView } from '@/components/orchestration/GeneratingLessonView';
import { VideoResultPage } from '@/components/pages/VideoResultPage';
import { CurriculumPlan, Storyboard, JobStatus } from '@/lib/api/client';
import { isJobInProgress, resolveVideoUrl } from '@/lib/utils/jobUtils';
import { useJobStore, selectJobActions } from '@/lib/store/useJobStore';
import { useShallow } from 'zustand/react/shallow';
import { Button } from '@/components/ui/Common';
import { Outlet } from '@tanstack/react-router';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  const errorMessage = error instanceof Error ? error.message : String(error);
  return (
    <div className="min-h-md flex flex-col items-center justify-center px-4 text-center">
      <div className="bg-destructive/10 text-destructive dark:bg-destructive/30 mb-6 flex h-16 w-16 items-center justify-center rounded-full">
        <AlertTriangle className="h-8 w-8" />
      </div>
      <h2 className="text-foreground mb-3 text-xl font-bold">Something went wrong</h2>
      <p className="text-text-muted mb-6 max-w-md font-mono text-sm whitespace-pre-wrap">
        {errorMessage}
      </p>
      <Button onClick={resetErrorBoundary} className="px-8">
        Try again
      </Button>
    </div>
  );
}

interface OrchestratorViewProps {
  job: JobStatus | null;
  connectionState: 'connecting' | 'connected' | 'error' | 'closed';
  streamError: Error | string | null;
  locationPathname: string;
}

/**
 * OrchestratorView manages the high-level conditional rendering for active jobs.
 * This separates the "active generation" logic from the main App shell.
 */
export function OrchestratorView({
  job,
  connectionState,
  streamError,
  locationPathname,
}: OrchestratorViewProps) {
  const { resetJob } = useJobStore(useShallow(selectJobActions));
  const isAtHome = locationPathname === '/';

  // If a job is actively progressing and we are on the home page, show the pipeline view
  if (job && isJobInProgress(job) && isAtHome) {
    return (
      <GeneratingLessonView job={job} streamState={connectionState} streamError={streamError} />
    );
  }

  // If a job is finished and we are on the home page, show the final result
  if (job?.status === 'completed' && job.plan && job.storyboard && isAtHome) {
    return (
      <VideoResultPage
        videoUrl={resolveVideoUrl(job.video_url)}
        conceptTitle={job.plan.concept_title || 'Concept'}
        plan={job.plan as CurriculumPlan}
        storyboard={job.storyboard as Storyboard}
        manimCode={job.manim_code}
        durationSeconds={job.duration_seconds}
        videoMetadata={job.video_metadata}
        onReset={resetJob}
      />
    );
  }

  // Otherwise, render the standard route content
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Outlet />
    </ErrorBoundary>
  );
}
