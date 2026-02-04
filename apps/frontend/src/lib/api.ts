export interface TeachingStep {
    step_id: number;
    concept: string;
    visual_metaphor: string;
    narration: string;
}

export interface CurriculumPlan {
    concept_title: string;
    target_audience: string;
    teaching_steps: TeachingStep[];
}

export type JobStatusEnum = "planning" | "validating" | "architecting" | "rendering" | "reviewing" | "completed" | "failed";

export interface JobStatus {
    job_id: string;
    status: JobStatusEnum;
    current_step?: string;
    artifacts?: Record<string, any>;
    plan?: CurriculumPlan;
    error?: string;
    mode?: 'live' | 'mock';
}

export interface CreateJobRequest {
    topic: string;
    target_audience?: string;
}

export async function createJob(data: CreateJobRequest): Promise<JobStatus> {
    const response = await fetch('/api/jobs/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error('Failed to create job');
    }
    return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`/api/jobs/${jobId}/status`);
    if (!response.ok) {
        throw new Error('Failed to get job status');
    }
    return response.json();
}

export async function getJobPlan(jobId: string): Promise<CurriculumPlan> {
    const response = await fetch(`/api/jobs/${jobId}/plan`);
    if (!response.ok) {
        throw new Error('Failed to get job plan');
    }
    return response.json();
}
