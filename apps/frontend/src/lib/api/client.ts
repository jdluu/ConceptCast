import { MOCK_JOBS_SUMMARY, MOCK_JOB_DETAILS } from '@/lib/api/mock';
import type { components } from '@/lib/api/schema';
import {
    type JobStatus,
    type JobSummary,
    type JobRequest,
    type ThoughtLog,
    type CurriculumPlan,
    type Storyboard,
    type TeachingStep,
    type Scene
} from '@/lib/api/types';

export const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '';

export {
    type JobStatus,
    type JobSummary,
    type JobRequest,
    type ThoughtLog,
    type CurriculumPlan,
    type Storyboard,
    type TeachingStep,
    type Scene
};

export async function listJobs(): Promise<{ jobs: JobSummary[] }> {
    const response = await fetch(`${API_BASE_URL}/jobs`);
    if (!response.ok) throw new Error('Failed to fetch jobs');
    const data = await response.json();
    
    // Always include mock data in the response; the UI will filter it based on Developer Mode
    return {
        jobs: [...data.jobs, ...MOCK_JOBS_SUMMARY]
    };
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
    if (jobId.startsWith('mock-')) {
        const mockDetail = MOCK_JOB_DETAILS[jobId];
        if (mockDetail) return mockDetail;
        throw new Error('Mock job not found');
    }
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/status`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
}

export async function createJob(request: JobRequest): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}/jobs/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to create job');
    return response.json();
}

export async function retryJob(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/retry`, {
        method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to retry job');
    return response.json();
}

export async function deleteJob(jobId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete job');
}

export async function getAvailableModels(): Promise<components["schemas"]["AvailableModelsResponse"]> {
    const response = await fetch(`${API_BASE_URL}/models`);
    if (!response.ok) throw new Error('Failed to get available models');
    return response.json();
}
