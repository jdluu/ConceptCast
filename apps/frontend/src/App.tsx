import { useEffect, useCallback } from 'react';
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
    <div className="flex min-h-md flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 text-destructive dark:bg-destructive/30">
        <AlertTriangle className="h-8 w-8" />
      </div>
      <h2 className="mb-3 text-xl font-bold text-foreground">Something went wrong</h2>
      <p className="mb-6 max-w-md font-mono text-sm whitespace-pre-wrap text-text-muted">
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
  const { setRenderProgress, resetJob } = useJobStore(useShallow(selectJobActions));

  const { theme } = useTheme();
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const location = useRouterState({ select: (s) => s.location });

  // Live job state from backend
  const {
    jobStatus: liveJobStatus,
    connectionState,
    error: streamError,
  } = useJobEvents(initialJob?.job_id);

  const job = liveJobStatus ?? initialJob;

  // Helper for browser notifications
  const sendNotification = useCallback(
    (title: string, body: string) => {
      if (!settings.enableNotifications) return;

      if (Notification.permission === 'granted') {
        void new Notification(title, { body, icon: '/favicon.ico' });
      } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then((permission) => {
          if (permission === 'granted') {
            void new Notification(title, { body, icon: '/favicon.ico' });
          }
        });
      }
    },
    [settings.enableNotifications],
  );

  // Helper for sound effects
  const playSound = useCallback(
    (type: 'success' | 'error' | 'info') => {
      if (!settings.enableSound) return;

      const frequencies = {
        success: [440, 880],
        error: [220, 110],
        info: [660],
      };

      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;
        const notes = frequencies[type];

        notes.forEach((freq, i) => {
          osc.frequency.setValueAtTime(freq, now + i * 0.1);
        });

        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.3);

        osc.start(now);
        osc.stop(now + 0.3);
      } catch (e) {
        console.warn('Audio effects not supported or blocked', e);
      }
    },
    [settings.enableSound],
  );

  // Use real progress from backend if available, else fallback to simulation
  const realProgress = job?.render_progress || 0;

  useEffect(() => {
    if (job?.status === 'rendering') {
      if (realProgress > 0) {
        setRenderProgress(realProgress);
        return;
      }
      // Fallback simulation if real progress hasn't started yet
      const interval = window.setInterval(() => {
        setRenderProgress((prev) => (prev >= 95 ? prev : prev + (100 - prev) * 0.05));
      }, 2000);
      return () => clearInterval(interval);
    } else if (!job || job.status === 'completed' || job.status === 'failed') {
      setRenderProgress(0);
    }
  }, [job?.status, realProgress, setRenderProgress]);

  // Background notifications
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
    // Only intercept with the generation view if we are on the dashboard/initial page ('/')
    // This allows users to navigate to /jobs or /settings even when a job is active.
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
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Consult the Council
        </h1>
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
