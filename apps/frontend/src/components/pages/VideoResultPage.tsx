import { useState, useRef, useEffect } from 'react';
import type { CurriculumPlan, Storyboard, TeachingStep, Scene } from '../../lib/api/client';

interface VideoResultPageProps {
    videoUrl: string | null;
    conceptTitle: string;
    plan: CurriculumPlan;
    storyboard: Storyboard;
    validation?: any;
    manimCode?: string | null;
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
        <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-sm transition-all duration-300">
            <button
                type="button"
                onClick={() => setOpen((o) => !o)}
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-[var(--background)]/50 transition-colors"
                aria-expanded={open}
            >
                <span className="font-bold text-[var(--foreground)] uppercase tracking-wider text-sm">{title}</span>
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className={`w-5 h-5 text-[var(--text-muted)] transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    aria-hidden
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
            </button>
            {open && <div className="px-6 pb-6 pt-0 animate-in slide-in-from-top-2 duration-300">{children}</div>}
        </div>
    );
}

export function VideoResultPage({ 
    videoUrl, 
    conceptTitle, 
    plan, 
    storyboard, 
    validation,
    manimCode,
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
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16 mx-auto mb-4 text-white/10" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <p className="text-lg font-bold text-white/40">Video not available</p>
                                <p className="text-sm text-white/20 mt-2 max-w-xs mx-auto">Mock runs skip rendering. Use a live provider to generate a video.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Artifact Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Validation / Critique (NEW) */}
                {validation && (
                    <CollapsiblePanel title="Analyst Review" defaultOpen={true}>
                        <div className="space-y-4">
                            <div className="flex items-center gap-3">
                                {validation.is_valid ? (
                                    <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-[10px] font-bold uppercase tracking-wider">
                                        Approved
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[10px] font-bold uppercase tracking-wider">
                                        Needs Adjustment
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-[var(--foreground)] leading-relaxed italic border-l-2 border-indigo-500/30 pl-4 py-1">
                                "{validation.feedback}"
                            </p>
                            {validation.suggestions?.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Suggestions</h4>
                                    <ul className="space-y-1.5">
                                        {validation.suggestions.map((s: string, i: number) => (
                                            <li key={i} className="text-xs text-[var(--text-muted)] flex gap-2">
                                                <span className="text-indigo-500">•</span>
                                                {s}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </CollapsiblePanel>
                )}

                {/* 2. Curriculum Plan */}
                <CollapsiblePanel title="Curriculum Plan" defaultOpen={true}>
                    <ul className="space-y-6">
                        {plan.teaching_steps.map((step: TeachingStep) => (
                            <li key={step.step_id} className="group/step">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="w-6 h-6 rounded bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold shadow-sm">{step.step_id}</span>
                                    <h3 className="font-bold text-[var(--foreground)] group-hover/step:text-indigo-600 dark:group-hover/step:text-indigo-400 transition-colors">{step.concept}</h3>
                                </div>
                                <p className="text-sm text-[var(--text-muted)] pl-9 leading-relaxed italic opacity-80">
                                    {step.visual_metaphor}
                                </p>
                            </li>
                        ))}
                    </ul>
                </CollapsiblePanel>

                {/* 3. Visual Storyboard */}
                <CollapsiblePanel title="Visual Storyboard" defaultOpen={true}>
                    <ul className="space-y-6">
                        {storyboard.scenes.map((scene: Scene) => (
                            <li key={scene.scene_id} className="group/scene">
                                <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-1 opacity-60">
                                    SCENE {scene.scene_id}
                                </div>
                                <h3 className="font-bold text-[var(--foreground)] group-hover/scene:text-indigo-600 dark:group-hover/scene:text-indigo-400 transition-colors uppercase tracking-tight text-sm">{scene.title}</h3>
                                <p className="text-sm text-[var(--text-muted)] mt-1.5 leading-relaxed">{scene.description}</p>
                            </li>
                        ))}
                    </ul>
                </CollapsiblePanel>

                {/* 4. Manim Code (NEW) */}
                {manimCode && (
                    <CollapsiblePanel title="Technical Script" defaultOpen={false}>
                        <div className="relative group/code">
                            <pre className="text-[11px] font-mono text-[var(--text-muted)] bg-black/40 p-4 rounded-xl overflow-x-auto max-h-[300px] custom-scrollbar border border-[var(--surface-border)]">
                                {manimCode}
                            </pre>
                            <div className="absolute top-3 right-3 opacity-0 group-hover/code:opacity-100 transition-opacity">
                                <span className="px-2 py-1 rounded bg-indigo-500/20 text-indigo-400 text-[9px] font-bold uppercase tracking-wider backdrop-blur-md border border-indigo-500/30">
                                    Python / Manim
                                </span>
                            </div>
                        </div>
                    </CollapsiblePanel>
                )}
            </div>
        </div>
    );
}
