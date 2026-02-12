import { useState, useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { JobCreationForm } from './components/forms/JobCreationForm';
import { CouncilLog } from './components/council/CouncilLog';
import { StoryboardView } from './components/council/StoryboardView';
import { VideoPreview } from './components/council/VideoPreview';
import { createJob, JobStatus, CreateJobRequest } from './lib/api';
import { useJobEvents } from './lib/hooks/useJobEvents';

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
                    
                    {currentJob?.plan && (
                        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                            <h3 className="text-md font-semibold text-white mb-4">Curriculum Plan</h3>
                            <div className="prose prose-invert prose-sm">
                                <h4 className="text-indigo-400">{currentJob.plan.concept_title}</h4>
                                <p className="text-neutral-400 text-xs mb-4">Audience: {currentJob.plan.target_audience}</p>
                                <ul className="space-y-2">
                                    {currentJob.plan.teaching_steps.map((step) => (
                                        <li key={step.step_id} className="bg-neutral-950 p-3 rounded border border-neutral-800">
                                            <div className="font-medium text-white">{step.step_id}. {step.concept}</div>
                                            <div className="text-xs text-neutral-500 mt-1">Metaphor: {step.visual_metaphor}</div>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}

                    {currentJob?.storyboard && (
                        <StoryboardView storyboard={currentJob.storyboard} />
                    )}

                    {currentJob?.video_url && (
                        <VideoPreview 
                            videoUrl={currentJob.video_url} 
                            conceptTitle={currentJob.plan?.concept_title || 'Rendering...'} 
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
