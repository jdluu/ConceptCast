import { CheckCircle2, XCircle, Clock, Square, Loader2 } from 'lucide-react';
import { JobStatus } from '@/lib/api/types';

interface StatusIconProps {
  status: JobStatus['status'];
  className?: string;
}

export function StatusIcon({ status, className = 'w-5 h-5' }: StatusIconProps) {
  switch (status) {
    case 'queued':
    case 'pending_retry':
      return <Clock className={`${className} text-text-muted`} />;
    case 'planning':
    case 'architecting':
    case 'rendering':
    case 'reviewing':
    case 'animating' as any:
      return <Loader2 className={`${className} text-council-active animate-spin`} />;
    case 'completed':
      return <CheckCircle2 className={`${className} text-council-completed`} />;
    case 'failed':
      return <XCircle className={`${className} text-destructive`} />;
    default:
      return <Square className={`${className} text-text-muted opacity-50`} />;
  }
}
