import { useState, useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { JobCreationForm } from './components/forms/JobCreationForm';
import { CouncilLog } from './components/council/CouncilLog';
import { StoryboardView } from './components/council/StoryboardView';
import { VideoPreview } from './components/council/VideoPreview';
import { createJob, JobStatus, CreateJobRequest } from './lib/api';

/**
 * Main application component.
 * 
 * Manages the state of the current job proposal and coordinates
 * the Job Creation and Council Log views.
 */
function App() {
    const [currentJob, setCurrentJob] = useState<JobStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const [renderProgress, setRenderProgress] = useState(0);

    // Subscribe via SSE for job status updates with reconnection logic
    useEffect(() => {
        if (!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') {
            setRenderProgress(0);
            return;
        }

        let eventSource: EventSource | null = null;
        let retryTimeout: number | null = null;
        let retryCount = 0;

        const connect = () => {
            if (eventSource) eventSource.close();
            
            console.log(`Connecting to SSE (attempt ${retryCount + 1})...`);
            eventSource = new EventSource(`/api/jobs/${currentJob.job_id}/events`);
            
            eventSource.onopen = () => {
                retryCount = 0; // Reset on success
                console.log('SSE Connected');
            };

            eventSource.onmessage = (event) => {
                const status = JSON.parse(event.data);
                setCurrentJob(status);
                
                if (status.status === 'completed' || status.status === 'failed') {
                    eventSource?.close();
                }
            };

            eventSource.onerror = (error) => {
                console.error('SSE Error:', error);
                eventSource?.close();
                
                // Retry logic with exponential backoff (max 30s)
                const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
                retryCount++;
                
                console.log(`Retrying SSE in ${delay}ms...`);
                retryTimeout = window.setTimeout(connect, delay);
            };
        };

        connect();

        // Simulated progress interval for rendering phase
        let progressInterval: number | null = null;
        if (currentJob.status === 'rendering') {
            progressInterval = window.setInterval(() => {
                setRenderProgress(prev => {
                    if (prev >= 95) return prev;
                    return prev + (100 - prev) * 0.05; // Asymptotic progress
                });
            }, 2000);
        }

        return () => {
            if (eventSource) eventSource.close();
            if (retryTimeout) clearTimeout(retryTimeout);
            if (progressInterval) clearInterval(progressInterval);
        };
    }, [currentJob?.job_id, currentJob?.status === 'completed', currentJob?.status === 'failed', currentJob?.status === 'rendering']);

    const handleCreateJob = async (data: CreateJobRequest) => {
        setIsLoading(true);
        try {
            const job = await createJob(data);
            setCurrentJob(job);
        } catch (error) {
            console.error('Failed to create job:', error);
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
