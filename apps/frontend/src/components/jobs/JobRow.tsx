import { type JobSummary, type JobStatus } from '@/lib/api/client';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { JobDetailPanel } from '@/components/jobs/JobDetailPanel';
import { ActionButton } from '@/components/ui/ActionButton';
import { cn } from '@/lib/utils';
import { 
    Play, 
    RotateCcw, 
    Download, 
    Trash2, 
    ChevronDown, 
    ChevronUp,
    CheckSquare,
    Square,
    Clock,
    PlayCircle,
    Loader2
} from 'lucide-react';
import { formatDuration, formatGenerationTime } from '@/lib/utils/durationUtils';

export interface JobRowProps {
    job: JobSummary;
    isExpanded: boolean;
    isSelected: boolean;
    detail?: JobStatus;
    onToggleExpand: () => void;
    onToggleSelect: () => void;
    onDelete: () => void;
    onRetry: () => void;
    onPlay: () => void;
}

const formatTime = (isoString: string | null | undefined) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

/**
 * A single expandable row in the Jobs table.
 *
 * Displays a job summary with preview, status, duration, output metadata,
 * model info, and action buttons. Expands to show the full JobDetailPanel.
 *
 * @param {JobRowProps} props - Component properties.
 * @returns {JSX.Element} The rendered table row (plus optional detail row).
 */
export function JobRow({ job, isExpanded, isSelected, detail, onToggleExpand, onToggleSelect, onDelete, onRetry, onPlay }: JobRowProps) {
    const metadata = (job as any).video_metadata || {};

    return (
        <>
            <tr className={cn(
                "group transition-all duration-200 cursor-pointer",
                isExpanded ? "bg-indigo-500/5" : "hover:bg-[var(--surface-border)]/20",
                isSelected && "bg-indigo-500/5"
            )} onClick={onToggleExpand}>
                <td className="pl-6 pr-4 py-5" onClick={(e) => { e.stopPropagation(); onToggleSelect(); }}>
                    <button className={cn("p-1 transition-colors", isSelected ? "text-indigo-500" : "text-[var(--text-muted)] group-hover:text-[var(--foreground)]")}>
                        {isSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                    </button>
                </td>
                <td className="px-4 py-5">
                    <div className="w-20 aspect-video rounded-md bg-[var(--background)] border border-[var(--surface-border)] overflow-hidden relative shadow-inner">
                        {job.thumbnail_url ? (
                            <img src={job.thumbnail_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center">
                                <Play className="w-4 h-4 text-[var(--text-muted)]" />
                            </div>
                        )}
                    </div>
                </td>
                <td className="px-4 py-5 max-w-xs">
                    <span className="block font-semibold text-[var(--foreground)] truncate">{job.topic}</span>
                    <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5 uppercase tracking-tighter">{job.job_id.split('-')[0]}</span>
                </td>
                <td className="px-4 py-5">
                    <StatusBadge status={job.status as any} />
                </td>
                <td className="px-4 py-5 font-medium whitespace-nowrap">
                    <div className="flex flex-col">
                        <span className="text-[var(--foreground)] text-xs flex items-center gap-1.5">
                            <PlayCircle className="w-3 h-3 text-indigo-500/50" />
                            {formatDuration(Number(metadata.duration))}
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1.5">
                            <Clock className="w-2.5 h-2.5" />
                            {formatGenerationTime(job.duration_seconds)}
                        </span>
                    </div>
                </td>
                <td className="px-4 py-5">
                    <div className="flex flex-col">
                        <span className="text-[var(--foreground)] font-medium text-xs">
                            {job.resolution ? (
                                metadata.resolution && metadata.resolution !== job.resolution 
                                    ? `${job.resolution} (${metadata.resolution})`
                                    : job.resolution
                            ) : (metadata.resolution || '\u2014')}
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)]">
                            {metadata.file_size || (job.frame_rate ? `${job.frame_rate} FPS` : '')}
                        </span>
                    </div>
                </td>
                <td className="px-4 py-5 text-right">
                    <span className="block text-indigo-600 dark:text-indigo-400 font-bold">{job.model_id || '\u2014'}</span>
                </td>
                <td className="px-4 py-5 text-right whitespace-nowrap">
                    <span className="block text-[var(--foreground)] opacity-80">{new Date(job.created_at).toLocaleDateString()}</span>
                    <span className="block text-[10px] text-[var(--text-muted)]">{formatTime(job.created_at)}</span>
                </td>
                <td className="pl-4 pr-6 py-5 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 px-1">
                        {job.status === 'completed' && <ActionButton icon={<Play className="w-3.5 h-3.5" />} title="Play" onClick={onPlay} />}
                        {job.status === 'failed' && <ActionButton icon={<RotateCcw className="w-3.5 h-3.5" />} title="Retry" onClick={onRetry} />}
                        {job.status === 'completed' && <ActionButton icon={<Download className="w-3.5 h-3.5" />} title="Download" onClick={() => {}} />}
                        <ActionButton icon={<Trash2 className="w-3.5 h-3.5" />} title="Delete" variant="danger" onClick={onDelete} />
                        <button 
                            onClick={(e) => { e.stopPropagation(); onToggleExpand(); }}
                            className="ml-2 pl-2 border-l border-[var(--surface-border)] hover:text-[var(--foreground)] transition-colors"
                        >
                            {isExpanded ? <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />}
                        </button>
                    </div>
                </td>
            </tr>
            {isExpanded && (
                <tr>
                    <td colSpan={9} className="p-0 border-b border-[var(--surface-border)]">
                        {detail ? <JobDetailPanel job={detail} /> : (
                            <div className="p-12 text-center bg-[var(--surface)]/50">
                                <Loader2 className="w-6 h-6 text-indigo-500 animate-spin mx-auto mb-2" />
                                <span className="text-[var(--text-muted)] text-sm">Loading job artifacts...</span>
                            </div>
                        )}
                    </td>
                </tr>
            )}
        </>
    );
}
