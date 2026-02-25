import { useQuery } from '@tanstack/react-query';
import { listJobs, type JobSummary } from '@/lib/api/client';

/**
 * TanStack Query hook for fetching the full job list.
 *
 * Polls every 5 seconds while the window is focused to surface new
 * or updated jobs without a manual refresh.
 *
 * @returns Query result containing `JobSummary[]`.
 */
export function useJobs() {
    return useQuery<{ jobs: JobSummary[] }>({
        queryKey: ['jobs'],
        queryFn: listJobs,
        refetchInterval: 5_000,
    });
}
