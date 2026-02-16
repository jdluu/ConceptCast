import { useEffect } from 'react';
import { Toaster, toast } from 'sonner';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { JobCreationForm } from './components/forms/JobCreationForm';
import { GeneratingLessonView } from './components/council/GeneratingLessonView';
import { LibraryPage } from './components/pages/LibraryPage';
import { SettingsPage } from './components/pages/SettingsPage';
import { JobsPage } from './components/pages/JobsPage';
import { VideoResultPage } from './components/pages/VideoResultPage';
import { API_BASE_URL, JobStatus, CurriculumPlan, Storyboard } from './lib/api/client';
import { useJobEvents } from './lib/hooks/useJobEvents';
import { useJobStore } from './lib/store/useJobStore';
import { useNavStore } from './lib/store/useNavStore';
import { ThemeProvider, useTheme } from './lib/contexts/theme';

/**
 * The root application component for ConceptCast.
 *
 * Orchestrates the global state for job generation, including SSE-based
 * real-time updates, simulated progress tracking, and view coordination
 * between job creation and result displays.
 */
const isJobInProgress = (job: JobStatus) =>
    job.status !== 'completed' && job.status !== 'failed';

/** Resolve video URL for playback: prepend API base when path is relative. */
function resolveVideoUrl(videoUrl: string | null | undefined): string | null {
    if (!videoUrl) return null;
    if (videoUrl.startsWith('http')) return videoUrl;
    const base = API_BASE_URL.replace(/\/$/, '');
    const path = videoUrl.startsWith('/') ? videoUrl : `/${videoUrl}`;
    return `${base}${path}`;
}

function AppContent() {
    // Stores
    const { 
        currentJob: initialJob, 
        setRenderProgress,
        resetJob
    } = useJobStore();
    
    const { currentNav } = useNavStore();
    const { theme } = useTheme();

    // Live job state from backend (GET /jobs/:id/status + SSE /jobs/:id/events)
    // We use the job_id from the store's initialJob
    const { jobStatus: liveJobStatus, connectionState, error: streamError } = useJobEvents(initialJob?.job_id);
    
    // The "source of truth" for the current job state is the live status if available, else the fallback
    const job = liveJobStatus ?? initialJob;

    useEffect(() => {
        if (job?.status === 'rendering') {
            const interval = window.setInterval(() => {
                setRenderProgress(prev => {
                    if (prev >= 95) return prev;
                    return prev + (100 - prev) * 0.05; // Asymptotic progress
                });
            }, 2000);
            return () => clearInterval(interval);
        } else if (!job || job.status === 'completed' || job.status === 'failed') {
            setRenderProgress(0);
        }
    }, [job?.status, setRenderProgress]);

    // Handle background errors/success via toasts
    useEffect(() => {
        if (job?.status === 'failed' && job.error) {
            toast.error(`Generation failed: ${job.error}`);
        }
        if (job?.status === 'completed') {
            toast.success('Animation completed! Loading results...');
        }
    }, [job?.status, job?.error]);

    const showGeneratingView = job && isJobInProgress(job);

    const showVideoResultPage =
        job?.status === 'completed' &&
        job.plan &&
        job.storyboard;

    const plan = job?.plan as unknown as CurriculumPlan | null;
    const storyboard = job?.storyboard as unknown as Storyboard | null;

    const mainContent = () => {
        if (currentNav === 'jobs') return <JobsPage />;
        if (currentNav === 'library') return <LibraryPage />;
        if (currentNav === 'settings') return <SettingsPage />;
        
        if (showGeneratingView) {
            return (
                <GeneratingLessonView
                    job={job!}
                    streamState={connectionState}
                    streamError={streamError}
                />
            );
        }

        if (showVideoResultPage) {
            return (
                <VideoResultPage
                    videoUrl={resolveVideoUrl(job.video_url)}
                    conceptTitle={plan?.concept_title || 'Concept'}
                    plan={plan!}
                    storyboard={storyboard!}
                    validation={job.validation}
                    manimCode={job.manim_code}
                    durationSeconds={job.duration_seconds}
                    videoMetadata={job.video_metadata}
                    onReset={resetJob}
                />
            );
        }

        return (
            <div className="max-w-3xl mx-auto">
                <header className="mb-8">
                    <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Consult the Council</h1>
                </header>

                <section className="mb-12">
                    <JobCreationForm />
                </section>
            </div>
        );
    };

    return (
        <>
            <Toaster position="top-right" richColors theme={theme === 'system' ? 'system' : theme} />
            <DashboardLayout>
                {mainContent()}
            </DashboardLayout>
        </>
    );
}

function App() {
    return (
        <ThemeProvider>
            <AppContent />
        </ThemeProvider>
    );
}

export default App;
