import { useEffect } from 'react';
import { Toaster, toast } from 'sonner';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { JobCreationForm } from '@/components/forms/JobCreationForm';
import { GeneratingLessonView } from '@/components/orchestration/GeneratingLessonView';
import { LibraryPage } from '@/components/pages/LibraryPage';
import { SettingsPage } from '@/components/pages/SettingsPage';
import { JobsPage } from '@/components/pages/JobsPage';
import { VideoResultPage } from '@/components/pages/VideoResultPage';
import { motion, AnimatePresence } from 'framer-motion';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { useJobEvents } from '@/lib/hooks/useJobEvents';
import { useJobStore } from '@/lib/store/useJobStore';
import { ThemeProvider, useTheme } from '@/lib/contexts/theme';
import { isJobInProgress, resolveVideoUrl } from '@/lib/utils/jobUtils';
import { createRootRoute, createRoute, createRouter, RouterProvider, Outlet, useRouterState } from '@tanstack/react-router';
import { ErrorBoundary, FallbackProps } from 'react-error-boundary';
import { AlertTriangle } from 'lucide-react';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center px-4">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center mb-6">
                <AlertTriangle className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-[var(--foreground)] mb-3">Something went wrong</h2>
            <p className="text-[var(--text-muted)] max-w-md mb-6 whitespace-pre-wrap font-mono text-sm">
                {errorMessage}
            </p>
            <button
                onClick={resetErrorBoundary}
                className="px-6 py-2 bg-[var(--foreground)] text-[var(--background)] rounded-xl font-medium hover:opacity-90 transition-opacity"
            >
                Try again
            </button>
        </div>
    );
}

/**
 * AppContent orchestrates the global state and view coordination.
 */
function AppContent() {
    const { 
        currentJob: initialJob, 
        setRenderProgress,
        resetJob
    } = useJobStore();
    
    const { theme } = useTheme();
    const location = useRouterState({ select: (s) => s.location });

    // Live job state from backend
    const { jobStatus: liveJobStatus, connectionState, error: streamError } = useJobEvents(initialJob?.job_id);
    
    const job = liveJobStatus ?? initialJob;

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
                setRenderProgress(prev => (prev >= 95 ? prev : prev + (100 - prev) * 0.05));
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
        }
        if (job?.status === 'completed') {
            toast.success('Animation completed! Loading results...');
        }
    }, [job?.status, job?.error]);

    const renderMainContent = () => {
        // Only intercept with the generation view if we are on the dashboard/initial page ('/')
        // This allows users to navigate to /jobs or /settings even when a job is active.
        const isAtHome = location.pathname === '/';

        if (job && isJobInProgress(job) && isAtHome) {
            return (
                <GeneratingLessonView
                    job={job}
                    streamState={connectionState}
                    streamError={streamError}
                />
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
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
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
        <div className="max-w-3xl mx-auto">
            <header className="mb-8">
                <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Consult the Council</h1>
            </header>
            <JobCreationForm />
        </div>
    );
}

// Router Configuration
const rootRoute = createRootRoute({
    component: AppContent
});

const indexRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/',
    component: IndexView
});

const jobsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/jobs',
    component: JobsPage
});

const libraryRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/library',
    component: LibraryPage
});

const settingsRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: '/settings',
    component: SettingsPage
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
