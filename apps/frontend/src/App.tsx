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
import { useNavStore } from '@/lib/store/useNavStore';
import { ThemeProvider, useTheme } from '@/lib/contexts/theme';
import { isJobInProgress, resolveVideoUrl } from '@/lib/utils/jobUtils';

/**
 * AppContent orchestrates the global state and view coordination.
 */
function AppContent() {
    const { 
        currentJob: initialJob, 
        setRenderProgress,
        resetJob
    } = useJobStore();
    
    const { currentNav } = useNavStore();
    const { theme } = useTheme();

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
        if (currentNav === 'jobs') return <JobsPage />;
        if (currentNav === 'library') return <LibraryPage />;
        if (currentNav === 'settings') return <SettingsPage />;
        
        if (job && isJobInProgress(job)) {
            return (
                <GeneratingLessonView
                    job={job}
                    streamState={connectionState}
                    streamError={streamError}
                />
            );
        }

        if (job?.status === 'completed' && job.plan && job.storyboard) {
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
            <div className="max-w-3xl mx-auto">
                <header className="mb-8">
                    <h1 className="text-2xl font-bold text-[var(--foreground)] tracking-tight">Consult the Council</h1>
                </header>
                <JobCreationForm />
            </div>
        );
    };

    return (
        <>
            <Toaster position="top-right" richColors theme={theme === 'system' ? 'system' : theme} />
            <DashboardLayout>
                <AnimatePresence mode="wait">
                    <motion.div
                        key={currentNav + (job?.job_id ?? '')}
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

function App() {
    return (
        <ThemeProvider>
            <AppContent />
        </ThemeProvider>
    );
}

export default App;
