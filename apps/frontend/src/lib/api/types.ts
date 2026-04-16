import type { components } from '@/lib/api/schema';

export interface VideoMetadata {
  resolution: string;
  duration: number;
  bitrate: string;
  file_size: string;
  format: string;
  fps?: number;
  width?: number;
  height?: number;
}

export type JobStatus = Omit<components['schemas']['JobStatus'], 'status'> & {
  topic?: string | null;
  status: components['schemas']['JobStatus']['status'] | 'queued';
  cost?: number;
  thumbnail_url?: string | null;
  preview_url?: string | null;
  video_metadata?: VideoMetadata | null;
  render_progress?: number;
};
export type JobSummary = components['schemas']['JobSummary'] & {
  cost?: number;
  thumbnail_url?: string | null;
  preview_url?: string | null;
  video_url?: string | null;
  video_metadata?: VideoMetadata | null;
  render_progress?: number;
};
export type JobRequest = components['schemas']['JobRequest'];
export type ThoughtLog = components['schemas']['ThoughtLog'];
export type CurriculumPlan = components['schemas']['CurriculumPlan'];
export type Storyboard = components['schemas']['Storyboard'];
export type TeachingStep = components['schemas']['TeachingStep'];
export type Scene = components['schemas']['Scene'];
