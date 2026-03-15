import { MOCK_JOBS_SUMMARY, MOCK_JOB_DETAILS } from '@/lib/api/mock';
import type { paths, components } from '@/lib/api/schema';
import createClient from 'openapi-fetch';
import {
  type JobStatus,
  type JobSummary,
  type JobRequest,
  type ThoughtLog,
  type CurriculumPlan,
  type Storyboard,
  type TeachingStep,
  type Scene,
} from '@/lib/api/types';

export interface JobReviewRequest {
  feedback?: string;
  edited_plan?: CurriculumPlan;
  action: 'approve' | 'regenerate';
}

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || '';

const apiClient = createClient<paths>({ baseUrl: API_BASE_URL });

export {
  type JobStatus,
  type JobSummary,
  type JobRequest,
  type ThoughtLog,
  type CurriculumPlan,
  type Storyboard,
  type TeachingStep,
  type Scene,
};

export async function listJobs(): Promise<{ jobs: JobSummary[] }> {
  const { data, error } = await apiClient.GET('/jobs');
  if (error) throw new Error('Failed to fetch jobs');

  const jobs = import.meta.env.DEV
    ? [...((data?.jobs || []) as JobSummary[]), ...MOCK_JOBS_SUMMARY]
    : ((data?.jobs || []) as JobSummary[]);
  return { jobs };
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  if (jobId.startsWith('mock-')) {
    const mockDetail = MOCK_JOB_DETAILS[jobId];
    if (mockDetail) return mockDetail;
    throw new Error('Mock job not found');
  }
  const { data, error } = await apiClient.GET('/jobs/{job_id}/status', {
    params: { path: { job_id: jobId } },
  });
  if (error) throw new Error('Failed to fetch job status');
  return data as unknown as JobStatus;
}

export async function createJob(request: JobRequest): Promise<JobStatus> {
  const { data, error } = await apiClient.POST('/jobs/create', {
    body: request as components['schemas']['JobRequest'],
  });
  if (error) throw new Error('Failed to create job');
  return data as unknown as JobStatus;
}

export async function retryJob(jobId: string): Promise<JobStatus> {
  // The endpoint might be /jobs/{job_id}/retry, checking assuming standard schema
  const { data, error } = await apiClient.POST('/jobs/{job_id}/retry' as any, {
    params: { path: { job_id: jobId } as any },
  });
  if (error) throw new Error('Failed to retry job');
  return data as unknown as JobStatus;
}

export async function deleteJob(jobId: string): Promise<void> {
  const { error } = await apiClient.DELETE('/jobs/{job_id}', {
    params: { path: { job_id: jobId } },
  });
  if (error) throw new Error('Failed to delete job');
}

export async function deleteAllJobs(): Promise<void> {
  const { error } = await apiClient.DELETE('/jobs');
  if (error) throw new Error('Failed to clear job history');
}

export async function reviewJob(jobId: string, review: JobReviewRequest): Promise<JobStatus> {
  const { data, error } = await apiClient.POST('/jobs/{job_id}/review' as any, {
    params: { path: { job_id: jobId } as any },
    body: review as any,
  });
  if (error) throw new Error('Failed to submit review');
  return data as unknown as JobStatus;
}

export async function getAvailableModels(): Promise<
  components['schemas']['AvailableModelsResponse']
> {
  const { data, error } = await apiClient.GET('/models', {});
  if (error) throw new Error('Failed to get available models');
  return data as components['schemas']['AvailableModelsResponse'];
}
