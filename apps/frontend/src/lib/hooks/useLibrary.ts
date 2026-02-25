import { useQuery } from '@tanstack/react-query';
import { listJobs, type JobSummary } from '@/lib/api/client';

/**
 * TanStack Query hook for fetching completed jobs (the "library").
 *
 * Filters the full job list to only completed entries. Refetches on
 * window focus but does not poll, since library content is less volatile.
 *
 * @returns Query result containing completed `JobSummary[]`.
 */
export function useLibrary() {
    return useQuery<JobSummary[]>({
        queryKey: ['library'],
        queryFn: async () => {
            const data = await listJobs();
            return data.jobs.filter(j => j.status === 'completed');
        },
    });
}
