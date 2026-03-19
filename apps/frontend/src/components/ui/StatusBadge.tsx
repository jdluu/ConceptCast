import { JobStatus } from '@/lib/api/types';
import { StatusIcon } from '@/components/ui/StatusIcon';

const statusLabels: Record<string, string> = {
  planning: 'Planning',
  architecting: 'Architecting',
  animating: 'Animating',
  rendering: 'Rendering',
  reviewing: 'Reviewing',
  completed: 'Completed',
  failed: 'Failed',
  queued: 'Queued',
  pending_retry: 'Pending Retry',
};

const statusColors: Record<string, string> = {
  planning: 'bg-agent-planning/10 text-agent-planning border-agent-planning/20',
  architecting: 'bg-agent-architecting/10 text-agent-architecting border-agent-architecting/20',
  animating: 'bg-agent-animating/10 text-agent-animating border-agent-animating/20',
  rendering: 'bg-agent-rendering/10 text-agent-rendering border-agent-rendering/20',
  reviewing: 'bg-agent-reviewing/10 text-agent-reviewing border-agent-reviewing/20',
  completed: 'bg-council-completed/10 text-council-completed border-council-completed/20',
  failed: 'bg-destructive/10 text-destructive border-destructive/20',
  queued: 'bg-surface-border/20 text-text-muted border-surface-border/40',
  pending_retry: 'bg-warning/10 text-warning border-warning/20',
};

interface StatusBadgeProps {
  status: JobStatus['status'];
  showIcon?: boolean;
  className?: string;
}

export function StatusBadge({ status, showIcon = true, className = '' }: StatusBadgeProps) {
  return (
    <span
      className={`text-mini inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-bold ${statusColors[status] || 'border-surface-border/40 bg-surface-border/20 text-text-muted'} ${className}`}
    >
      {showIcon && <StatusIcon status={status} className="h-3 w-3" />}
      {statusLabels[status] || status}
    </span>
  );
}
