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

/**
 * Enhanced JobStatus that extends the generated schema with client-side
 * helpers and resolved metadata.
 */
export type JobStatus = components['schemas']['JobStatus'] & {
  // Add missing fields from schema generation
  topic?: string | null;
  preview_url?: string | null;
  video_metadata?: VideoMetadata | null;
};

export type JobSummary = components['schemas']['JobSummary'] & {
  video_metadata?: VideoMetadata | null;
};

export type JobRequest = components['schemas']['JobRequest'];
export type ThoughtLog = components['schemas']['ThoughtLog'];
export type CurriculumPlan = components['schemas']['CurriculumPlan'];
export type Storyboard = components['schemas']['Storyboard'];
export type TeachingStep = components['schemas']['TeachingStep'];
export type Scene = components['schemas']['Scene'];
export type VisualObject = components['schemas']['VisualObject'];
