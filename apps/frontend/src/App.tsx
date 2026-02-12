import { useState, useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { JobCreationForm } from './components/forms/JobCreationForm';
import { CouncilLog } from './components/council/CouncilLog';
import { StoryboardView } from './components/council/StoryboardView';
import { VideoPreview } from './components/council/VideoPreview';
import { createJob, JobStatus, CreateJobRequest, CurriculumPlan, Storyboard } from './lib/api';
import { useJobEvents } from './lib/hooks/useJobEvents';

import { CurriculumPlanDisplay } from './components/council/CurriculumPlanDisplay';

/**
 * The root application component for ConceptCast.
 *
 * Orchestrates the global state for job generation, including SSE-based
 * real-time updates, simulated progress tracking, and view coordination
 * between job creation and result displays.
 */
function App() {
    const [initialJob, setInitialJob] = useState<JobStatus | null>(null);
    const { jobStatus: liveJobStatus } = useJobEvents(initialJob?.job_id);
    const currentJob = liveJobStatus || initialJob;

    const [isLoading, setIsLoading] = useState(false);
    const [renderProgress, setRenderProgress] = useState(0);

    const plan = currentJob?.plan as unknown as CurriculumPlan | null;
    const storyboard = currentJob?.storyboard as unknown as Storyboard | null;

    useEffect(() => {
        if (currentJob?.status === 'rendering') {
            const interval = window.setInterval(() => {
                setRenderProgress(prev => {
                    if (prev >= 95) return prev;
                    return prev + (100 - prev) * 0.05; // Asymptotic progress
                });
            }, 2000);
            return () => clearInterval(interval);
        } else if (!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') {
            setRenderProgress(0);
        }
    }, [currentJob?.status]);

    /**
     * Initiates a new video generation job and updates global state.
     *
     * @param data - The job request parameters including topic and audience.
     */
    const handleCreateJob = async (data: CreateJobRequest) => {
        setIsLoading(true);
        try {
            const job = await createJob(data);
            setInitialJob(job);
        } catch {
            alert('Failed to initiate job. Check console.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-8">
                    <JobCreationForm 
                        onSubmit={handleCreateJob} 
                        isLoading={isLoading} 
                    />
                    
                    {plan && (
                        <CurriculumPlanDisplay plan={plan} />
                    )}

                    {storyboard && (
                        <StoryboardView storyboard={storyboard} />
                    )}

                    {currentJob?.video_url && (
                        <VideoPreview 
                            videoUrl={currentJob.video_url} 
                            conceptTitle={plan?.concept_title || 'Rendering...'} 
                        />
                    )}
                </div>

                <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white">Council Activity</h3>
                    <CouncilLog job={currentJob} renderProgress={renderProgress} />
                </div>
            </div>
        </DashboardLayout>
    );
}

export default App;
