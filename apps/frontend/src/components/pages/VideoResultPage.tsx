import { useRef, useEffect } from 'react';
import { ShieldCheck, Lightbulb, Video, Code, Clock, PlayCircle, Plus } from 'lucide-react';
import type { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { CollapsiblePanel } from '@/components/ui/CollapsiblePanel';
import { AnalystVerdict } from '@/components/orchestration/AnalystVerdict';
import { CurriculumTimeline } from '@/components/orchestration/CurriculumTimeline';
import { SceneGallery } from '@/components/orchestration/SceneGallery';
import { CodeWorkspace } from '@/components/orchestration/CodeWorkspace';
import { Button } from '@/components/ui/Common';
import { formatDuration, formatGenerationTime } from '@/lib/utils/durationUtils';

interface VideoResultPageProps {
  videoUrl: string | null;
  conceptTitle: string;
  plan: CurriculumPlan;
  storyboard: Storyboard;
  validation?: any;
  manimCode?: string | null;
  durationSeconds?: number | null;
  videoMetadata?: any | null;
  onReset: () => void;
}

/**
 * The final results page for a completed generation job.
 */
export function VideoResultPage({
  videoUrl,
  conceptTitle,
  plan,
  storyboard,
  validation,
  manimCode,
  durationSeconds,
  videoMetadata,
  onReset,
}: VideoResultPageProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoUrl && videoRef.current) videoRef.current.load();
  }, [videoUrl]);

  return (
    <div className="animate-in fade-in mx-auto max-w-5xl space-y-8 duration-500">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between">
        <h1 className="text-foreground text-3xl font-bold tracking-tight">{conceptTitle}</h1>
        <Button onClick={onReset} className="h-11 px-6">
          <Plus className="h-4 w-4" strokeWidth={3} />
          Create New Video
        </Button>
      </div>

      {/* Video metadata overview */}
      <div className="flex flex-wrap items-center gap-4 px-2">
        <div className="border-council-active/20 bg-council-active/10 flex items-center gap-2 rounded-full border px-3 py-1.5">
          <Clock className="text-council-active h-3.5 w-3.5" />
          <span className="text-mini text-council-active leading-none font-bold tracking-widest uppercase">
            Gen Time: {formatGenerationTime(durationSeconds)}
          </span>
        </div>
        {videoMetadata?.duration && (
          <div className="border-success/20 bg-success/10 flex items-center gap-2 rounded-full border px-3 py-1.5">
            <PlayCircle className="text-success h-3.5 w-3.5" />
            <span className="text-mini text-success leading-none font-bold tracking-widest uppercase">
              Duration: {formatDuration(Number(videoMetadata.duration))}
            </span>
          </div>
        )}
        {videoMetadata?.resolution && (
          <div className="text-tiny text-text-muted px-1 font-bold tracking-[0.2em] uppercase">
            {videoMetadata.resolution} {'\u2022'} {videoMetadata.file_size || 'N/A'}
          </div>
        )}
      </div>

      {/* Video player or placeholder at top */}
      <div className="border-surface-border bg-surface overflow-hidden rounded-3xl border shadow-2xl transition-all">
        <div className="relative aspect-video bg-black shadow-inner">
          {videoUrl ? (
            <video
              ref={videoRef}
              className="h-full w-full object-contain"
              controls
              autoPlay
              playsInline
            >
              <source src={videoUrl} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="px-6 text-center">
                <Video
                  className="text-text-muted mx-auto mb-4 h-16 w-16 opacity-20"
                  strokeWidth={1}
                />
                <p className="text-text-muted text-lg font-bold opacity-60">Video not available</p>
                <p className="text-text-muted mx-auto mt-2 max-w-xs text-sm opacity-40">
                  Mock runs skip rendering. Use a live provider to generate a video.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Artifact Panels */}
      <div className="grid grid-cols-1 gap-6 pb-20 lg:grid-cols-2">
        {validation && (
          <CollapsiblePanel title="Council Verdict" icon={ShieldCheck}>
            <AnalystVerdict validation={validation} />
          </CollapsiblePanel>
        )}

        <CollapsiblePanel title="Curriculum Timeline" icon={Lightbulb}>
          <CurriculumTimeline plan={plan} />
        </CollapsiblePanel>

        <CollapsiblePanel title="Visual Storyboard" icon={Video}>
          <SceneGallery storyboard={storyboard} />
        </CollapsiblePanel>

        {manimCode && (
          <CollapsiblePanel title="Technical Script" icon={Code} defaultOpen={false}>
            <CodeWorkspace code={manimCode} />
          </CollapsiblePanel>
        )}
      </div>
    </div>
  );
}
