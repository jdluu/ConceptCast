import type { components } from './schema';

export type JobStatus = Omit<components["schemas"]["JobStatus"], 'status'> & {
    topic?: string | null;
    status: components["schemas"]["JobStatus"]["status"] | "queued";
    cost?: number;
    thumbnail_url?: string | null;
    video_metadata?: any | null;
};
export type JobSummary = components["schemas"]["JobSummary"] & {
    cost?: number;
    thumbnail_url?: string | null;
    video_metadata?: any | null;
};
export type JobRequest = components["schemas"]["JobRequest"];
export type ThoughtLog = components["schemas"]["ThoughtLog"];
export type CurriculumPlan = components["schemas"]["CurriculumPlan"];
export type Storyboard = components["schemas"]["Storyboard"];
export type TeachingStep = components["schemas"]["TeachingStep"];
export type Scene = components["schemas"]["Scene"];
