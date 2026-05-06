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
  const { data, error } = await apiClient.GET('/jobs/', {});
  if (error) throw new Error('Failed to fetch jobs');

  const jobs = import.meta.env.DEV
    ? [...((data?.jobs || []) as JobSummary[]), ...MOCK_JOBS_SUMMARY]
    : ((data?.jobs || []) as JobSummary[]);
  return { jobs };
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  if (jobId.startsWith('mock-')) {
    const mockDetail = MOCK_JOB_DETAILS[jobId];
    if (mockDetail) return mockDetail as unknown as JobStatus;
    throw new Error('Mock job not found');
  }
  const { data, error } = await apiClient.GET('/jobs/{job_id}/status', {
    params: { path: { job_id: jobId } },
  });
  if (error) throw new Error('Failed to fetch job status');
  return data as JobStatus;
}

export async function createJob(request: JobRequest): Promise<JobStatus> {
  const { data, error } = await apiClient.POST('/jobs/create', {
    body: request,
  });
  if (error) throw new Error('Failed to create job');
  return data as JobStatus;
}

/**
 * Retries a failed or stuck job from the last successful checkpoint.
 *
 * @param jobId - The unique identifier of the job to retry.
 * @returns The updated JobStatus after resetting for retry.
 */
export async function retryJob(jobId: string): Promise<JobStatus> {
  const { data, error } = await apiClient.POST('/jobs/{job_id}/retry', {
    params: { path: { job_id: jobId } },
  });
  if (error) throw new Error('Failed to retry job');
  return data as JobStatus;
}

/**
 * Deletes a job and its associated filesystem data.
 *
 * @param jobId - The unique identifier of the job to delete.
 */
export async function deleteJob(jobId: string): Promise<void> {
  const { error } = await apiClient.DELETE('/jobs/{job_id}', {
    params: { path: { job_id: jobId } },
  });
  if (error) throw new Error('Failed to delete job');
}

/**
 * Deletes all jobs and clears the entire job history.
 */
export async function deleteAllJobs(): Promise<void> {
  const { error } = await apiClient.DELETE('/jobs/', {});
  if (error) throw new Error('Failed to clear job history');
}

/**
 * Handles human-in-the-loop review actions for a paused job.
 *
 * @param jobId - The unique identifier of the job being reviewed.
 * @param review - The feedback and action (approve/regenerate) from the user.
 * @returns The updated JobStatus after processing the review.
 */
export async function reviewJob(jobId: string, review: JobReviewRequest): Promise<JobStatus> {
  const { data, error } = await apiClient.POST('/jobs/{job_id}/review', {
    params: { path: { job_id: jobId } },
    body: review as components['schemas']['JobReviewRequest'],
  });
  if (error) throw new Error('Failed to submit review');
  return data as JobStatus;
}

export async function getAvailableModels(): Promise<
  components['schemas']['AvailableModelsResponse']
> {
  const { data, error } = await apiClient.GET('/models', {});
  if (error) throw new Error('Failed to get available models');
  return data as components['schemas']['AvailableModelsResponse'];
}
