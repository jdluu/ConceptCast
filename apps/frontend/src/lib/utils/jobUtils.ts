import { API_BASE_URL, JobStatus } from '@/lib/api/client';

/**
 * Checks if a job is currently in progress.
 */
export const isJobInProgress = (job: JobStatus) =>
    job.status !== 'completed' && job.status !== 'failed';

/**
 * Resolves a video URL for playback, prepending the API base when the path is relative.
 */
export function resolveVideoUrl(videoUrl: string | null | undefined): string | null {
    if (!videoUrl) return null;
    if (videoUrl.startsWith('http')) return videoUrl;
    const base = API_BASE_URL.replace(/\/$/, '');
    const path = videoUrl.startsWith('/') ? videoUrl : `/${videoUrl}`;
    return `${base}${path}`;
}
