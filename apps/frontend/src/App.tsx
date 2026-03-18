import { useEffect } from 'react';
import { Toaster, toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { JobCreationForm } from '@/components/forms/JobCreationForm';
import { GeneratingLessonView } from '@/components/orchestration/GeneratingLessonView';
import { LibraryPage } from '@/components/pages/LibraryPage';
import { SettingsPage } from '@/components/pages/SettingsPage';
import { JobsPage } from '@/components/pages/JobsPage';
import { VideoResultPage } from '@/components/pages/VideoResultPage';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { useJobEvents } from '@/lib/hooks/useJobEvents';
import { useJobStore, selectCurrentJob, selectJobActions } from '@/lib/store/useJobStore';
import { useShallow } from 'zustand/react/shallow';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { ThemeProvider, useTheme } from '@/lib/contexts/theme';
import { isJobInProgress, resolveVideoUrl } from '@/lib/utils/jobUtils';
import { useAudioEffects } from '@/lib/hooks/useAudioEffects';
import { useNotifications } from '@/lib/hooks/useNotifications';
import { useRenderProgress } from '@/lib/hooks/useRenderProgress';
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  Outlet,
  useRouterState,
} from '@tanstack/react-router';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Common';

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

/**
 * AppContent orchestrates the global state and view coordination.
 */
function AppContent() {
  const initialJob = useJobStore(selectCurrentJob);
  const { resetJob } = useJobStore(useShallow(selectJobActions));

  const { theme } = useTheme();
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const location = useRouterState({ select: (s) => s.location });

  const { playSound } = useAudioEffects();
  const { sendNotification } = useNotifications();

  // Live job state from backend
  const {
    jobStatus: liveJobStatus,
    connectionState,
    error: streamError,
  } = useJobEvents(initialJob?.job_id);

  const job = liveJobStatus ?? initialJob;

  // Sync rendering progress from backend or simulation
  useRenderProgress(job?.status, job?.render_progress);

  // Background notifications and sound effects
  useEffect(() => {
    if (job?.status === 'failed' && job.error) {
      toast.error(`Generation failed: ${job.error}`);
      sendNotification('Generation Failed', `Job "${job.topic}" encountered an error.`);
      playSound('error');
    }
    if (job?.status === 'completed') {
      toast.success('Animation completed! Loading results...');
      sendNotification('Animation Ready', `"${job.topic}" has been successfully synthesized.`);
      playSound('success');
    }
  }, [job?.status, job?.error, job?.topic, sendNotification, playSound]);

  const renderMainContent = () => {
    const isAtHome = location.pathname === '/';

    if (job && isJobInProgress(job) && isAtHome) {
      return (
        <GeneratingLessonView job={job} streamState={connectionState} streamError={streamError} />
      );
    }

    if (job?.status === 'completed' && job.plan && job.storyboard && isAtHome) {
      const plan = job.plan as unknown as CurriculumPlan;
      const storyboard = job.storyboard as unknown as Storyboard;
      return (
        <VideoResultPage
          videoUrl={resolveVideoUrl(job.video_url)}
          conceptTitle={plan.concept_title || 'Concept'}
          plan={plan}
          storyboard={storyboard}
          validation={job.validation}
          manimCode={job.manim_code}
          durationSeconds={job.duration_seconds}
          videoMetadata={job.video_metadata}
          onReset={resetJob}
        />
      );
    }

    return (
      <ErrorBoundary FallbackComponent={ErrorFallback}>
        <Outlet />
      </ErrorBoundary>
    );
  };

  return (
    <>
      <Toaster position="top-right" richColors theme={theme === 'system' ? 'system' : theme} />
      <DashboardLayout>
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname + (job?.job_id ?? '')}
            initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, y: -10 }}
            transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
          >
            {renderMainContent()}
          </motion.div>
        </AnimatePresence>
      </DashboardLayout>
    </>
  );
}

// Ensure the JobCreationForm is wrapped nicely
function IndexView() {
  return (
    <div className="mx-auto max-w-3xl">
      <header className="mb-8">
        <h1 className="text-foreground text-2xl font-bold tracking-tight">Consult the Council</h1>
      </header>
      <JobCreationForm />
    </div>
  );
}

// Router Configuration
const rootRoute = createRootRoute({
  component: AppContent,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: IndexView,
});

const jobsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/jobs',
  component: JobsPage,
});

const libraryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/library',
  component: LibraryPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
});

const routeTree = rootRoute.addChildren([indexRoute, jobsRoute, libraryRoute, settingsRoute]);

const router = createRouter({ routeTree });

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return (
    <ThemeProvider>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

export default App;
