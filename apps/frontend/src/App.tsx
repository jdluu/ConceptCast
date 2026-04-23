import { useEffect, useRef } from 'react';
import { Toaster, toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ChatLaunchForm } from '@/components/forms/ChatLaunchForm';
import { LibraryPage } from '@/components/pages/LibraryPage';
import { SettingsPage } from '@/components/pages/SettingsPage';
import { JobsPage } from '@/components/pages/JobsPage';
import { LazyMotion, domAnimation, AnimatePresence, useReducedMotion } from 'motion/react';
import * as m from 'motion/react-m';
import { useJobEvents } from '@/lib/hooks/useJobEvents';
import { useJobStore, selectCurrentJob } from '@/lib/store/useJobStore';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { ThemeProvider, useTheme } from '@/lib/contexts/theme';
import { useAudioEffects } from '@/lib/hooks/useAudioEffects';
import { useNotifications } from '@/lib/hooks/useNotifications';
import { useRenderProgress } from '@/lib/hooks/useRenderProgress';
import { OrchestratorView } from '@/components/orchestration/OrchestratorView';
import {
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
  useRouterState,
} from '@tanstack/react-router';

/**
 * AppContent orchestrates the global state and shell coordination.
 */
function AppContent() {
  const initialJob = useJobStore(selectCurrentJob);
  const { theme } = useTheme();
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const location = useRouterState({ select: (s) => s.location });

  const { playSound } = useAudioEffects();
  const { sendNotification } = useNotifications();

  // Tracks which job+status pairs have already triggered notifications
  // to prevent replaying on rehydration or HMR remounts.
  const notifiedRef = useRef<string | null>(null);

  // On mount, clear stale terminal-state jobs from the persisted store.
  // A persisted "failed" or "completed" job should not keep the user
  // locked into the generation view on a fresh page load.
  useEffect(() => {
    if (
      initialJob &&
      (initialJob.status === 'completed' || initialJob.status === 'failed')
    ) {
      notifiedRef.current = `${initialJob.job_id}:${initialJob.status}`;
      useJobStore.getState().resetJob();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps -- mount-only reconciliation

  // Live job state from backend via SSE
  const {
    jobStatus: liveJobStatus,
    connectionState,
    error: streamError,
  } = useJobEvents(initialJob?.job_id);

  const job = liveJobStatus ?? initialJob;

  // Sync rendering progress from backend or simulation
  useRenderProgress(job?.status, job?.render_progress);

  // Background notifications and sound effects for status changes.
  // Deduplicates using a ref to prevent replaying on rehydration.
  useEffect(() => {
    if (!job) return;

    const notificationKey = `${job.job_id}:${job.status}`;
    if (notifiedRef.current === notificationKey) return;

    if (job.status === 'failed' && job.error) {
      notifiedRef.current = notificationKey;
      toast.error(`Generation failed: ${job.error}`);
      sendNotification('Generation Failed', `Job "${job.topic}" encountered an error.`);
      playSound('error');
    }
    if (job.status === 'completed') {
      notifiedRef.current = notificationKey;
      toast.success('Animation completed! Loading results...');
      sendNotification('Animation Ready', `"${job.topic}" has been successfully synthesized.`);
      playSound('success');
    }
  }, [job?.status, job?.error, job?.topic, job?.job_id, sendNotification, playSound]);

  return (
    <>
      <Toaster position="top-right" richColors theme={theme === 'system' ? 'system' : theme} />
      <DashboardLayout>
        <AnimatePresence mode="wait">
          <LazyMotion features={domAnimation}>
            <m.div
              key={location.pathname + (job?.job_id ?? '')}
              initial={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={prefersReducedMotion ? { opacity: 1 } : { opacity: 0, y: -10 }}
              transition={{ duration: prefersReducedMotion ? 0 : 0.2 }}
            >
              <OrchestratorView
                job={job}
                connectionState={connectionState}
                streamError={streamError}
                locationPathname={location.pathname}
              />
            </m.div>
          </LazyMotion>
        </AnimatePresence>
      </DashboardLayout>
    </>
  );
}

// Ensure the JobCreationForm is wrapped nicely
function IndexView() {
  return <ChatLaunchForm />;
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
