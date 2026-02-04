import { useState, useEffect } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { JobCreationForm } from './components/forms/JobCreationForm';
import { CouncilLog } from './components/council/CouncilLog';
import { createJob, getJobStatus, JobStatus, CreateJobRequest } from './lib/api';

/**
 * Main application component.
 * 
 * Manages the state of the current job proposal and coordinates
 * the Job Creation and Council Log views.
 */
function App() {
    const [currentJob, setCurrentJob] = useState<JobStatus | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Poll for job status updates
    useEffect(() => {
        if (!currentJob || currentJob.status === 'completed' || currentJob.status === 'failed') return;

        const interval = setInterval(async () => {
            try {
                const status = await getJobStatus(currentJob.job_id);
                setCurrentJob(status);
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [currentJob]);

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
                </div>

                <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-white">Council Activity</h3>
                    <CouncilLog job={currentJob} />
                </div>
            </div>
        </DashboardLayout>
    );
}

export default App;
