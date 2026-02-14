import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { JobStatus, getJobStatus, API_BASE_url } from '../api';

interface UseJobEventsReturn {
    jobStatus: JobStatus | null;
    connectionState: 'connecting' | 'connected' | 'error' | 'closed';
    error: Error | null;
}

export function useJobEvents(jobId: string | undefined): UseJobEventsReturn {
    const queryClient = useQueryClient();
    const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'error' | 'closed'>('closed');
    const [error, setError] = useState<Error | null>(null);

    const { data: jobStatus } = useQuery<JobStatus>({
        queryKey: ['job', jobId],
        queryFn: () => getJobStatus(jobId!),
        enabled: !!jobId,
        staleTime: Infinity, // Primary updates via SSE
        refetchInterval: (query) => {
            const data = query.state.data;
            const status = data?.status;
            if (status === 'completed' || status === 'failed') return false;
            return 3000; // Fallback poll every 3s while job in progress
        },
    });
    
    // Refs to keep track of retry logic without triggering re-renders
    const retryCount = useRef(0);
    const retryTimeout = useRef<number | null>(null);
    const eventSource = useRef<EventSource | null>(null);

    const connect = useCallback(() => {
        if (!jobId) return;

        // Cleanup previous connection if exists
        if (eventSource.current) {
            eventSource.current.close();
        }

        setConnectionState('connecting');
        
        try {
            const es = new EventSource(`${API_BASE_url}/jobs/${jobId}/events`);
            eventSource.current = es;

            es.onopen = () => {
                setConnectionState('connected');
                retryCount.current = 0;
                setError(null);
            };

            es.onmessage = (event) => {
                try {
                    const status = JSON.parse(event.data);
                    queryClient.setQueryData(['job', jobId], status);

                    if (status.status === 'completed' || status.status === 'failed') {
                        es.close();
                        setConnectionState('closed');
                    }
                } catch (err) {
                    console.error('Failed to parse SSE message', err);
                }
            };

            es.onerror = () => {
                es.close();
                setConnectionState('error');
                
                // Exponential backoff
                const delay = Math.min(1000 * Math.pow(2, retryCount.current), 30000);
                retryCount.current++;
                
                retryTimeout.current = window.setTimeout(connect, delay);
            };

        } catch (err) {
            setError(err instanceof Error ? err : new Error('Unknown error connecting to SSE'));
            setConnectionState('error');
        }
    }, [jobId]);

    useEffect(() => {
        if (jobId) {
            connect();
        } else {
            setConnectionState('closed');
        }

        return () => {
            if (eventSource.current) {
                eventSource.current.close();
            }
            if (retryTimeout.current) {
                clearTimeout(retryTimeout.current);
            }
        };
    }, [jobId, connect]);

    return { jobStatus: jobStatus || null, connectionState, error };
}
