import { JobStatus } from '../../lib/api/types';
import { StatusIcon } from './StatusIcon';

const statusLabels: Record<string, string> = {
    planning: 'Planning',
    validating: 'Validating',
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
    planning: 'bg-blue-400/10 text-blue-400 border-blue-400/20',
    validating: 'bg-purple-400/10 text-purple-400 border-purple-400/20',
    architecting: 'bg-indigo-400/10 text-indigo-400 border-indigo-400/20',
    animating: 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20',
    rendering: 'bg-yellow-400/10 text-yellow-400 border-yellow-400/20',
    reviewing: 'bg-orange-400/10 text-orange-400 border-orange-400/20',
    completed: 'bg-green-400/10 text-green-400 border-green-400/20',
    failed: 'bg-red-400/10 text-red-400 border-red-400/20',
    queued: 'bg-neutral-400/10 text-neutral-400 border-neutral-400/20',
    pending_retry: 'bg-amber-400/10 text-amber-400 border-amber-400/20',
};

interface StatusBadgeProps {
    status: JobStatus['status'];
    showIcon?: boolean;
    className?: string;
}

export function StatusBadge({ status, showIcon = true, className = "" }: StatusBadgeProps) {
    return (
        <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border ${statusColors[status] || 'bg-neutral-400/10 text-neutral-400 border-neutral-400/20'} ${className}`}>
            {showIcon && <StatusIcon status={status} className="w-3 h-3" />}
            {statusLabels[status] || status}
        </span>
    );
}
