import { useState, useRef, useEffect } from 'react';
import type { CurriculumPlan, Storyboard, TeachingStep, Scene } from '../../lib/api';

interface VideoResultPageProps {
    videoUrl: string | null;
    conceptTitle: string;
    plan: CurriculumPlan;
    storyboard: Storyboard;
    onReset: () => void;
}

function CollapsiblePanel({
    title,
    children,
    defaultOpen = true,
}: {
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);

    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
            <button
                type="button"
                onClick={() => setOpen((o) => !o)}
                className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-neutral-800/50 transition-colors"
                aria-expanded={open}
            >
                <span className="font-semibold text-white">{title}</span>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className={`w-5 h-5 text-neutral-400 transition-transform ${open ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
            </button>
            {open && <div className="px-5 pb-5 pt-0">{children}</div>}
        </div>
    );
}

export function VideoResultPage({ videoUrl, conceptTitle: _conceptTitle, plan, storyboard, onReset }: VideoResultPageProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoUrl && videoRef.current) videoRef.current.load();
    }, [videoUrl]);

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            {/* Header with Back Button */}
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-semibold text-white">Generation Result</h1>
                <button
                    onClick={onReset}
                    className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Create New Video
                </button>
            </div>

            {/* Video player or placeholder at top */}
            <div className="bg-neutral-900 border border-neutral-700 rounded-lg overflow-hidden">
                <div className="relative aspect-video bg-black">
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
                        <div className="absolute inset-0 flex items-center justify-center text-neutral-500">
                            <div className="text-center px-6">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12 mx-auto mb-3 text-neutral-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <p className="text-sm font-medium text-neutral-400">Video not available</p>
                                <p className="text-xs text-neutral-500 mt-1">Mock runs skip rendering. Use a live provider to generate a video.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Two collapsible panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CollapsiblePanel title="Curriculum Plan" defaultOpen={true}>
                    <ul className="space-y-4">
                        {plan.teaching_steps.map((step: TeachingStep) => (
                            <li key={step.step_id} className="border-b border-neutral-800 pb-4 last:border-0 last:pb-0">
                                <div className="font-medium text-white">
                                    {step.step_id}. {step.concept}
                                </div>
                                <div className="text-sm text-neutral-500 mt-0.5">
                                    Metaphor: {step.visual_metaphor}
                                </div>
                            </li>
                        ))}
                    </ul>
                </CollapsiblePanel>

                <CollapsiblePanel title="Visual Storyboard" defaultOpen={true}>
                    <ul className="space-y-4">
                        {storyboard.scenes.map((scene: Scene) => (
                            <li key={scene.scene_id} className="border-b border-neutral-800 pb-4 last:border-0 last:pb-0">
                                <div className="text-xs font-mono text-neutral-500 uppercase tracking-wider mb-0.5">
                                    SCENE {scene.scene_id}
                                </div>
                                <div className="font-medium text-white">{scene.title}</div>
                                <p className="text-sm text-neutral-400 mt-0.5">{scene.description}</p>
                            </li>
                        ))}
                    </ul>
                </CollapsiblePanel>
            </div>
        </div>
    );
}
