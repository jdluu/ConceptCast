import { useRef, useEffect } from 'react';
import { 
    ShieldCheck, 
    Lightbulb, 
    Video, 
    Code, 
    Clock,
    PlayCircle
} from 'lucide-react';
import type { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { CollapsiblePanel } from '@/components/ui/CollapsiblePanel';
import { AnalystVerdict } from '@/components/orchestration/AnalystVerdict';
import { CurriculumTimeline } from '@/components/orchestration/CurriculumTimeline';
import { SceneGallery } from '@/components/orchestration/SceneGallery';
import { CodeWorkspace } from '@/components/orchestration/CodeWorkspace';
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
 *
 * Renders the video player, metadata badges, and collapsible panels
 * for the council verdict, curriculum timeline, storyboard, and code.
 *
 * @param {VideoResultPageProps} props - Component properties.
 * @returns {JSX.Element} The rendered video result page.
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
    onReset 
}: VideoResultPageProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoUrl && videoRef.current) videoRef.current.load();
    }, [videoUrl]);

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header with Back Button */}
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">{conceptTitle}</h1>
                <button
                    onClick={onReset}
                    className="h-11 px-6 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/20 active:scale-95"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                    Create New Video
                </button>
            </div>

            {/* Video metadata overview */}
            <div className="flex flex-wrap gap-4 items-center px-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                    <Clock className="w-3.5 h-3.5 text-indigo-500" />
                    <span className="text-[11px] font-bold text-indigo-500 uppercase tracking-widest leading-none">
                        Gen Time: {formatGenerationTime(durationSeconds)}
                    </span>
                </div>
                {videoMetadata?.duration && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                        <PlayCircle className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest leading-none">
                            Duration: {formatDuration(Number(videoMetadata.duration))}
                        </span>
                    </div>
                )}
                {videoMetadata?.resolution && (
                    <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-widest px-1">
                        {videoMetadata.resolution} {'\u2022'} {videoMetadata.file_size || 'N/A'}
                    </div>
                )}
            </div>

            {/* Video player or placeholder at top */}
            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-3xl overflow-hidden shadow-2xl transition-all">
                <div className="relative aspect-video bg-black shadow-inner">
                    {videoUrl ? (
                        <video
                            ref={videoRef}
                            className="w-full h-full object-contain"
                            controls
                            autoPlay
                            playsInline
                        >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="text-center px-6">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16 mx-auto mb-4 text-[var(--text-muted)] opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <p className="text-lg font-bold text-[var(--text-muted)] opacity-60">Video not available</p>
                                <p className="text-sm text-[var(--text-muted)] opacity-40 mt-2 max-w-xs mx-auto">Mock runs skip rendering. Use a live provider to generate a video.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Artifact Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-20">
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
