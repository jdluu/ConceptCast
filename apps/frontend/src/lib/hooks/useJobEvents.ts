import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { type JobStatus, getJobStatus, API_BASE_URL } from '@/lib/api/client';
import { useJobStore } from '@/lib/store/useJobStore';

interface UseJobEventsReturn {
  jobStatus: JobStatus | null;
  connectionState: 'connecting' | 'connected' | 'error' | 'closed';
  error: Error | null;
  cancelJob: () => void;
}

export function useJobEvents(jobId: string | undefined): UseJobEventsReturn {
  const queryClient = useQueryClient();
  const [connectionState, setConnectionState] = useState<
    'connecting' | 'connected' | 'error' | 'closed'
  >('closed');
  const [error, setError] = useState<Error | null>(null);

  const { data: jobStatus, error: queryError } = useQuery<JobStatus>({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    staleTime: Infinity, // Primary updates via WebSocket
    refetchInterval: (query) => {
      const data = query.state.data;
      const status = data?.status;
      if (status === 'completed' || status === 'failed') return false;
      return 3000; // Fallback poll every 3s while job in progress
    },
    retry: false, // Don't retry if job not found
  });

  useEffect(() => {
    if (
      queryError &&
      (queryError.message.includes('not found') || queryError.message.includes('404'))
    ) {
      const { resetJob } = useJobStore.getState();
      resetJob();
    }
  }, [queryError]);

  // Refs to keep track of retry logic and socket without triggering re-renders
  const retryCount = useRef(0);
  const retryTimeout = useRef<number | null>(null);
  const socket = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!jobId) return;

    // Cleanup previous connection if exists
    if (socket.current) {
      socket.current.close();
    }

    setConnectionState('connecting');

    try {
      const wsBaseUrl = API_BASE_URL.replace(/^http/, 'ws');
      const wsUrl = `${wsBaseUrl}/jobs/${jobId}/control`;
      const ws = new WebSocket(wsUrl);
      socket.current = ws;

      ws.addEventListener('open', () => {
        setConnectionState('connected');
        retryCount.current = 0;
        setError(null);
      });

      ws.addEventListener('message', (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'ping') {
            return;
          }

          if (data.error === 'Job not found') {
            const { resetJob } = useJobStore.getState();
            resetJob();
            ws.close();
            setConnectionState('closed');
            return;
          }

          const status = data as JobStatus;
          queryClient.setQueryData(['job', jobId], status);

          if (status.status === 'completed' || status.status === 'failed') {
            ws.close();
            setConnectionState('closed');
          }
        } catch (parseError) {
          console.error('Failed to parse WebSocket message', parseError);
        }
      });

      ws.addEventListener('error', (err) => {
        console.error('WebSocket connection error:', err);
        setError(new Error('WebSocket connection error'));
        setConnectionState('error');
      });

      ws.addEventListener('close', () => {
        // Only retry if the connection was not closed intentionally on completion/failure
        const currentData = queryClient.getQueryData<JobStatus>(['job', jobId]);
        const isFinished = currentData?.status === 'completed' || currentData?.status === 'failed';

        if (!isFinished) {
          setConnectionState('error');

          // Jittered exponential backoff: delay = min(30s, base * 2^retryCount)
          const baseDelay = 1000;
          const maxDelay = 30000;
          const calculatedDelay = Math.min(maxDelay, baseDelay * Math.pow(2, retryCount.current));
          const jitteredDelay = calculatedDelay / 2 + Math.random() * (calculatedDelay / 2);
          retryCount.current++;

          if (retryTimeout.current) {
            window.clearTimeout(retryTimeout.current);
          }
          retryTimeout.current = window.setTimeout(connect, jitteredDelay);
        } else {
          setConnectionState('closed');
        }
      });
    } catch (connError) {
      setError(
        connError instanceof Error ? connError : new Error('Unknown error connecting to WebSocket'),
      );
      setConnectionState('error');
    }
  }, [jobId, queryClient]);

  const cancelJob = useCallback(() => {
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ action: 'cancel' }));
    }
  }, []);

  useEffect(() => {
    if (jobId) {
      connect();
    } else {
      setConnectionState('closed');
    }

    return () => {
      if (socket.current) {
        socket.current.close();
      }
      if (retryTimeout.current) {
        clearTimeout(retryTimeout.current);
      }
    };
  }, [jobId, connect]);

  return { jobStatus: jobStatus || null, connectionState, error, cancelJob };
}
