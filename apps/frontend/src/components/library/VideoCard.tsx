import { Play, Download, Trash2, Calendar, Clock, PlayCircle } from 'lucide-react';
import { type JobSummary } from '@/lib/api/client';
import { Button } from '@/components/ui/Common';
import { formatDuration, formatGenerationTime } from '@/lib/utils/durationUtils';

interface VideoCardProps {
  job: JobSummary;
  onPlay: (jobId: string) => void;
  onDelete: (jobId: string) => void;
}

export function VideoCard({ job, onPlay, onDelete }: VideoCardProps) {
  return (
    <article className="group border-surface-border bg-surface hover:border-council-active/50 hover:shadow-council-active/5 relative flex flex-col overflow-hidden rounded-2xl border shadow-sm transition-all duration-500 hover:shadow-2xl">
      {/* Thumbnail Container */}
      <div className="bg-background relative aspect-video overflow-hidden shadow-inner">
        {job.thumbnail_url ? (
          <img
            src={job.thumbnail_url}
            alt=""
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
          />
        ) : (
          <div className="from-surface to-background flex h-full w-full items-center justify-center bg-gradient-to-br">
            <Play className="text-text-muted group-hover:text-council-active/30 h-12 w-12 opacity-20 transition-colors" />
          </div>
        )}

        {/* Overlay Gradient */}
        <div className="from-surface/90 absolute inset-0 bg-gradient-to-t via-transparent to-transparent opacity-60 transition-opacity group-hover:opacity-100" />

        {/* Duration Badge */}
        <div className="text-tiny absolute right-3 bottom-3 flex items-center gap-1.5 rounded border border-white/10 bg-black/80 px-2 py-1 font-bold tracking-wider text-white uppercase backdrop-blur-md">
          <PlayCircle className="text-council-active h-3 w-3" />
          {formatDuration(Number(job.video_metadata?.duration))}
        </div>

        {/* Hover Play Button */}
        <button
          onClick={() => onPlay(job.job_id)}
          className="absolute inset-0 flex translate-y-4 transform items-center justify-center opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100"
        >
          <div className="flex h-20 w-20 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white shadow-2xl backdrop-blur-xl transition-all hover:scale-110 active:scale-95">
            <Play className="h-8 w-8 fill-current" />
          </div>
        </button>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col p-6">
        <h2 className="text-foreground group-hover:text-council-active mb-2 line-clamp-2 text-lg leading-snug font-bold transition-colors">
          {job.topic}
        </h2>
        <div className="text-text-muted mb-6 flex flex-wrap items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {new Date(job.created_at).toLocaleDateString()}
          </span>
          <span className="bg-surface-border h-1 w-1 rounded-full" />
          <span className="flex items-center gap-1">
            <Clock className="text-council-active/50 h-3.5 w-3.5" />
            {formatGenerationTime(job.duration_seconds)} gen
          </span>
          <span className="bg-surface-border h-1 w-1 rounded-full" />
          <span className="text-tiny text-text-muted font-mono tracking-tighter uppercase opacity-80">
            {job.model_id?.split(':')[0] || 'Unknown'}
          </span>
        </div>

        <div className="mt-auto flex gap-3">
          <Button onClick={() => onPlay(job.job_id)} className="flex-1">
            <Play className="h-4 w-4 fill-current" />
            Play Now
          </Button>
          <button className="border-surface-border bg-background text-text-muted hover:bg-surface hover:text-council-active dark:hover:text-council-active flex h-11 w-11 items-center justify-center rounded-xl border shadow-sm transition-all active:scale-95">
            <Download className="h-4 w-4" />
          </button>
          <button
            onClick={() => onDelete(job.job_id)}
            className="border-surface-border bg-background text-text-muted hover:border-destructive/20 hover:bg-destructive/10 hover:text-destructive flex h-11 w-11 items-center justify-center rounded-xl border shadow-sm transition-all active:scale-95"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </article>
  );
}
