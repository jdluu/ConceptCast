import { useEffect } from 'react';
import { useJobStore, selectJobActions } from '@/lib/store/useJobStore';
import { useShallow } from 'zustand/react/shallow';

export function useRenderProgress(jobStatus?: string, realProgress: number = 0) {
  const { setRenderProgress } = useJobStore(useShallow(selectJobActions));

  useEffect(() => {
    if (jobStatus === 'rendering') {
      if (realProgress > 0) {
        setRenderProgress(realProgress);
        return;
      }
      // Fallback simulation if real progress hasn't started yet
      const interval = window.setInterval(() => {
        setRenderProgress((prev) => (prev >= 95 ? prev : prev + (100 - prev) * 0.05));
      }, 2000);
      return () => clearInterval(interval);
    } else if (!jobStatus || jobStatus === 'completed' || jobStatus === 'failed') {
      setRenderProgress(0);
    }
  }, [jobStatus, realProgress, setRenderProgress]);
}
