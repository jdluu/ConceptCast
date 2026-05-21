import { type JobSummary, type JobStatus } from '@/lib/api/client';
import { type VideoMetadata } from '@/lib/api/types';
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
 */
export function JobRow({
  job,
  isExpanded,
  isSelected,
  detail,
  onToggleExpand,
  onToggleSelect,
  onDelete,
  onRetry,
  onPlay,
}: JobRowProps) {
  const metadata = (job.video_metadata as Partial<VideoMetadata>) || {};

  return (
    <>
      <tr
        className={cn(
          'group cursor-pointer transition-all duration-200',
          isExpanded ? 'bg-council-active/5' : 'hover:bg-surface-border/20',
          isSelected && 'bg-council-active/5',
        )}
        onClick={onToggleExpand}
      >
        <td
          className="py-5 pr-4 pl-6"
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect();
          }}
        >
          <button
            className={cn(
              'p-1 transition-colors',
              isSelected ? 'text-council-active' : 'text-text-muted group-hover:text-foreground',
            )}
          >
            {isSelected ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
          </button>
        </td>
        <td className="px-4 py-5">
          <div className="border-surface-border bg-background relative aspect-video w-20 overflow-hidden rounded-md border shadow-inner">
            {job.thumbnail_url ? (
              <img src={job.thumbnail_url} alt="" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full w-full items-center justify-center">
                <Play className="text-text-muted h-4 w-4 opacity-30" />
              </div>
            )}
          </div>
        </td>
        <td className="max-w-[300px] px-4 py-5">
          <span
            className="text-foreground block truncate leading-snug font-semibold"
            title={job.topic}
          >
            {job.topic}
          </span>
          <span className="text-text-muted mt-1 block font-mono text-[10px] tracking-tight uppercase opacity-50">
            ID_{job.job_id.split('-')[0]}
          </span>
        </td>
        <td className="px-4 py-5">
          <StatusBadge status={job.status as any} />
        </td>
        <td className="px-4 py-5 font-medium whitespace-nowrap">
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <PlayCircle className="text-council-active/50 h-3 w-3" />
              <span className="text-tiny text-council-active/70 font-semibold uppercase">
                Video
              </span>
              <span className="text-foreground text-xs">
                {formatDuration(Number(metadata.duration))}
              </span>
            </div>
            <div className="mt-0.5 flex items-center gap-1.5">
              <Clock className="text-text-muted h-2.5 w-2.5" />
              <span className="text-micro text-text-muted font-semibold uppercase">AI</span>
              <span className="text-tiny text-text-muted">
                {formatGenerationTime(job.duration_seconds)}
              </span>
            </div>
          </div>
        </td>
        <td className="px-4 py-5">
          <div className="flex flex-col">
            <span className="text-foreground text-xs font-medium">
              {metadata.resolution || '1080p'}
            </span>
            <span className="text-tiny text-text-muted">{metadata.file_size || '60 FPS'}</span>
          </div>
        </td>
        <td className="max-w-[140px] px-4 py-5 text-right">
          <span
            className="text-council-active dark:text-council-active block truncate font-bold"
            title={job.model_id || undefined}
          >
            {job.model_id || '\u2014'}
          </span>
        </td>
        <td className="px-4 py-5 text-right whitespace-nowrap">
          <span className="text-foreground block opacity-80">
            {new Date(job.created_at).toLocaleDateString()}
          </span>
          <span className="text-tiny text-text-muted block">{formatTime(job.created_at)}</span>
        </td>
        <td className="w-[160px] py-5 pr-6 pl-4 text-right" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-end gap-1 px-1">
            {job.status === 'completed' && (
              <ActionButton icon={<Play className="h-3.5 w-3.5" />} title="Play" onClick={onPlay} />
            )}
            {job.status === 'failed' && (
              <ActionButton
                icon={<RotateCcw className="h-3.5 w-3.5" />}
                title="Retry"
                onClick={onRetry}
              />
            )}
            {job.status === 'completed' && (
              <ActionButton
                icon={<Download className="h-3.5 w-3.5" />}
                title="Download"
                onClick={() => {}}
              />
            )}
            <ActionButton
              icon={<Trash2 className="h-3.5 w-3.5" />}
              title="Delete"
              variant="danger"
              onClick={onDelete}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onToggleExpand();
              }}
              className="border-surface-border hover:text-foreground ml-2 border-l pl-2 transition-colors"
            >
              {isExpanded ? (
                <ChevronUp className="text-text-muted h-4 w-4" />
              ) : (
                <ChevronDown className="text-text-muted h-4 w-4" />
              )}
            </button>
          </div>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={9} className="border-surface-border border-b p-0">
            <JobDetailPanel jobId={job.job_id} initialData={detail} />
          </td>
        </tr>
      )}
    </>
  );
}
