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

export interface ValidationResult {
    is_valid: boolean;
    feedback: string;
    suggestions: string[];
}

export interface VisualObject {
    name: string;
    type: string;
    position: string;
    color?: string;
    label?: string;
}

export interface Scene {
    scene_id: number;
    title: string;
    description: string;
    narration: string;
    objects: VisualObject[];
}

export interface Storyboard {
    concept_title: string;
    scenes: Scene[];
}

export type JobStatusEnum = "planning" | "validating" | "architecting" | "rendering" | "reviewing" | "completed" | "failed";

export interface JobStatus {
    job_id: string;
    status: JobStatusEnum;
    current_step?: string;
    plan?: CurriculumPlan;
    validation?: ValidationResult;
    storyboard?: Storyboard;
    manim_code?: string;
    video_url?: string;
    error?: string;
    mode: 'live' | 'mock';
}

export interface ProviderModels {
    provider: string;
    models: string[];
}

export interface AvailableModelsResponse {
    available: ProviderModels[];
}

export interface CreateJobRequest {
    topic: string;
    target_audience?: string;
    provider?: string;
    model_id?: string;
}

export async function getAvailableModels(): Promise<AvailableModelsResponse> {
    const response = await fetch('/api/models/available');
    if (!response.ok) {
        throw new Error('Failed to fetch available models');
    }
    return response.json();
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
