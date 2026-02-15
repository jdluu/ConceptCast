import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { JobStatus, Storyboard, CurriculumPlan } from '../../lib/api/client';
import { useJobStore } from '../../lib/store/useJobStore';
import { useAppSettings } from '../../lib/contexts/app-settings';
import { PipelineSteps } from '../ui/PipelineSteps';
import { Modal } from '../ui/common';
import { VideoPlayer } from '../ui/VideoPlayer';
import { API_BASE_URL } from '../../lib/api/client';

const agentBadgeColors: Record<string, string> = {
    analyst: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    validator: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    architect: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
    animator: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
    reviewer: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
};

function currentActionLabel(job: JobStatus, storyboard: Storyboard | null): string {
    switch (job.status) {
        case 'planning':
            return 'Analyst: Creating curriculum plan';
        case 'validating':
            return 'Validator: Verifying plan';
        case 'architecting':
            return 'Architect: Building visual storyboard';
        case 'rendering':
            if (storyboard?.scenes?.[0]?.title) {
                return `Animator: Rendering '${storyboard.scenes[0].title}'`;
            }
            return 'Animator: Rendering video';
        case 'reviewing':
            return 'Reviewing output';
        default:
            return 'Processing...';
    }
}

type StreamState = 'connecting' | 'connected' | 'error' | 'closed';

function StreamIndicator({ state, error }: { state: StreamState; error: Error | null }) {
    if (state === 'closed') return null;
    return (
        <div className="flex items-center gap-2 shrink-0" title={error?.message}>
            {state === 'connecting' && (
                <span className="flex items-center gap-1.5 text-sm text-[var(--text-muted)]">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" aria-hidden />
                    Connecting…
                </span>
            )}
            {state === 'connected' && (
                <span className="flex items-center gap-1.5 text-sm text-emerald-500 font-medium">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" aria-hidden />
                    Live
                </span>
            )}
            {state === 'error' && (
                <span className="flex items-center gap-1.5 text-sm text-amber-500 font-medium">
                    <span className="w-2 h-2 rounded-full bg-amber-500" aria-hidden />
                    Reconnecting…
                </span>
            )}
        </div>
    );
}

interface LiveArtifactPreviewProps {
    plan: CurriculumPlan | null;
    storyboard: Storyboard | null;
    status: string;
    renderProgress: number;
    thoughts: Array<{ agent: string; phase: string; content: string }>;
}

function LiveArtifactPreview({ plan, storyboard, status, renderProgress, thoughts }: LiveArtifactPreviewProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const isRendering = status === 'rendering';
    const hasStoryboard = !!storyboard;
    const hasPlan = !!plan;

    const relevantThoughts = useMemo(() => {
        if (hasStoryboard) return [];
        if (hasPlan && status === 'architecting') {
             return thoughts.filter(t => t.agent === 'architect');
        }
        if (!hasPlan && status === 'planning') {
            return thoughts.filter(t => t.agent === 'analyst' || t.agent === 'validator');
        }
        return [];
    }, [hasPlan, hasStoryboard, status, thoughts]);

    return (
        <>
            <motion.div 
                layout
                className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-xl"
            >
                <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--surface-border)] bg-[var(--surface)]/50">
                    <div className="flex items-center gap-3">
                        <motion.span 
                            animate={{ opacity: [0.4, 1, 0.4] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            className="w-2 h-2 rounded-full bg-indigo-500" 
                        />
                        <span className="text-sm font-bold text-[var(--foreground)] tracking-wider uppercase">
                            {isRendering ? 'Rendering Preview' : hasStoryboard ? 'Visual Storyboard' : 'Curriculum Plan'}
                        </span>
                    </div>
                    {(hasPlan || hasStoryboard) && (
                        <button 
                            onClick={() => setIsModalOpen(true)}
                            className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 uppercase tracking-widest px-2 py-1 rounded hover:bg-indigo-500/10 transition-colors"
                        >
                            View Full
                        </button>
                    )}
                    {isRendering && (
                        <span className="text-xs font-mono text-indigo-400">
                            {Math.round(renderProgress)}% COMPLETE
                        </span>
                    )}
                </div>

                <div className="p-6 min-h-[300px] max-h-[500px] overflow-y-auto custom-scrollbar">
                    <AnimatePresence mode="wait">
                        {!hasPlan && !hasStoryboard && relevantThoughts.length === 0 ? (
                            <motion.div 
                                key="loading"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] space-y-4 py-24"
                            >
                                <div className="w-10 h-10 rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 animate-spin shadow-sm" />
                                <p className="text-sm font-medium italic">Agents are assembling the framework...</p>
                            </motion.div>
                        ) : (!hasPlan || (status === 'architecting' && !hasStoryboard)) && relevantThoughts.length > 0 ? (
                            <motion.div 
                                key="live-thoughts"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="space-y-4"
                            >
                                <div className="text-xs font-bold text-indigo-400/60 uppercase tracking-widest mb-4">Live Activity Stream</div>
                                {relevantThoughts.slice(-5).map((t, i) => (
                                    <motion.div 
                                        key={i}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="flex gap-4 items-start p-4 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] shadow-sm"
                                    >
                                        <div className={`shrink-0 px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border ${agentBadgeColors[t.agent]}`}>
                                            {t.agent}
                                        </div>
                                        <p className="text-[var(--foreground)] text-sm leading-relaxed opacity-90">{t.content}</p>
                                    </motion.div>
                                ))}
                                <div className="flex items-center gap-3 px-4">
                                    <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
                                    <span className="text-xs text-[var(--text-muted)] font-medium italic">Synthesizing artifacts...</span>
                                </div>
                            </motion.div>
                        ) : (hasStoryboard ? (
                            <motion.div 
                                key="storyboard"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                            >
                                {storyboard.scenes.slice(0, 4).map((scene) => (
                                    <div key={scene.scene_id} className="p-5 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] hover:border-indigo-500/50 transition-all shadow-sm group/scene">
                                        <div className="text-[10px] font-bold text-[var(--text-muted)] mb-2 tracking-widest uppercase">SCENE {scene.scene_id}</div>
                                        <h4 className="text-[var(--foreground)] text-sm font-bold mb-2 line-clamp-1 group-hover/scene:text-indigo-600 dark:group-hover/scene:text-indigo-400 transition-colors uppercase tracking-tight">{scene.title}</h4>
                                        <p className="text-[var(--text-muted)] text-xs line-clamp-2 leading-relaxed">{scene.description}</p>
                                    </div>
                                ))}
                                {storyboard.scenes.length > 4 && (
                                    <button 
                                        onClick={() => setIsModalOpen(true)}
                                        className="col-span-full py-4 border-2 border-dashed border-[var(--surface-border)] rounded-xl text-[var(--text-muted)] text-xs font-bold uppercase tracking-widest hover:bg-[var(--surface)] hover:text-indigo-500 transition-all active:scale-[0.99]"
                                    >
                                        + {storyboard.scenes.length - 4} more scenes. View Full Storyboard.
                                    </button>
                                )}
                            </motion.div>
                        ) : (
                            <motion.div 
                                key="plan"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-4"
                            >
                                {plan!.teaching_steps.slice(0, 5).map((step) => (
                                    <div key={step.step_id} className="flex gap-5 p-4 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] shadow-sm hover:border-indigo-500/30 transition-all">
                                        <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm border border-indigo-500/20">
                                            {step.step_id}
                                        </span>
                                        <div>
                                            <h3 className="text-[var(--foreground)] text-sm font-bold tracking-tight">{step.concept}</h3>
                                            <p className="text-[var(--text-muted)] text-xs mt-1.5 line-clamp-1 italic italic opacity-80">
                                                {step.visual_metaphor}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                                {plan!.teaching_steps.length > 5 && (
                                    <button 
                                        onClick={() => setIsModalOpen(true)}
                                        className="w-full py-3 text-[var(--text-muted)] text-xs font-bold uppercase tracking-widest hover:text-indigo-500 transition-colors"
                                    >
                                        View all {plan!.teaching_steps.length} steps in detail
                                    </button>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </motion.div>

            <Modal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                title={hasStoryboard ? 'Full Visual Storyboard' : 'Complete Curriculum Plan'}
            >
                {hasStoryboard ? (
                    <div className="space-y-8">
                        {storyboard!.scenes.map((scene) => (
                            <div key={scene.scene_id} className="space-y-3">
                                <div className="flex items-center gap-3">
                                    <span className="px-2 py-1 bg-indigo-500 text-white text-[10px] font-bold rounded">SCENE {scene.scene_id}</span>
                                    <h3 className="text-lg font-bold text-white">{scene.title}</h3>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-4 rounded-lg bg-neutral-800/50 border border-neutral-700">
                                        <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-2">Visual Composition</div>
                                        <p className="text-neutral-300 text-sm leading-relaxed">{scene.description}</p>
                                    </div>
                                    <div className="p-4 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                                        <div className="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-2">Narration Script</div>
                                        <p className="text-sm italic text-neutral-300">"{scene.narration}"</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : hasPlan ? (
                    <div className="space-y-6">
                        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-8">
                             <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-1">Target Audience</div>
                             <p className="text-white text-lg font-medium">{plan!.target_audience}</p>
                        </div>
                        {plan!.teaching_steps.map((step) => (
                            <div key={step.step_id} className="flex gap-6 p-4 rounded-xl hover:bg-neutral-800/40 transition-colors">
                                <div className="shrink-0 w-10 h-10 rounded-full bg-neutral-800 flex items-center justify-center text-white font-bold border border-neutral-700">
                                    {step.step_id}
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold text-white">{step.concept}</h3>
                                    <div className="flex flex-col gap-1">
                                         <p className="text-sm text-neutral-300 leading-relaxed"><span className="text-indigo-400 font-semibold italic">Metaphor:</span> {step.visual_metaphor}</p>
                                         <p className="text-sm text-neutral-400 mt-2 p-3 bg-neutral-800/50 rounded-lg border border-neutral-800 whitespace-pre-wrap"><span className="text-[10px] font-bold block mb-1 text-neutral-500">NARRATION</span>"{step.narration}"</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : null}
            </Modal>
        </>
    );
}

interface GeneratingLessonViewProps {
    job: JobStatus;
    streamState?: StreamState;
    streamError?: Error | null;
}

export function GeneratingLessonView({
    job,
    streamState = 'closed',
    streamError = null,
}: GeneratingLessonViewProps) {
    const { submittedTopic: topic, renderProgress } = useJobStore();

    if (!job) return null;

    const plan = job.plan as unknown as CurriculumPlan | null;
    const storyboard = job.storyboard as unknown as Storyboard | null;
    const currentLabel = currentActionLabel(job, storyboard);
    const rawThoughts = (job.streamed_thoughts ?? []) as Array<{ agent?: string; phase?: string; content?: string; ts?: string }>;
    
    const thoughts = useMemo(() => {
        const groups: Array<{ agent: string; phase: string; content: string }> = [];
        for (const t of rawThoughts) {
            const agent = t.agent ?? '';
            const phase = t.phase ?? 'output';
            const content = (t.content ?? '').trim();
            const last = groups[groups.length - 1];
            if (last && last.agent === agent && last.phase === phase) {
                last.content = (last.content + (last.content && content ? ' ' : '') + content).replace(/\s+/g, ' ').trim();
            } else {
                groups.push({ agent, phase, content });
            }
        }
        return groups;
    }, [rawThoughts]);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">
                        {topic || 'Untitled Concept'}
                    </h1>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 text-sm text-[var(--text-muted)] font-medium">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                            {currentLabel}
                        </div>
                        {(job.provider || job.target_audience) && (
                            <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-wider text-neutral-600">
                                <span className="w-1 h-1 rounded-full bg-neutral-800" />
                                {job.provider && (
                                    <span className="flex items-center gap-1.5">
                                        {job.provider}
                                        {job.model_id && <span className="text-neutral-700 lowercase">({job.model_id})</span>}
                                    </span>
                                )}
                                {job.provider && job.target_audience && <span className="w-1 h-1 rounded-full bg-neutral-800" />}
                                {job.target_audience && <span className="truncate max-w-[200px]">{job.target_audience}</span>}
                            </div>
                        )}
                    </div>
                </div>
                <StreamIndicator state={streamState} error={streamError} />
            </header>

            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-3xl p-8 backdrop-blur-sm shadow-sm transition-all">
                <PipelineSteps status={job.status} />
            </div>

            {job.video_url ? (
                <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-2xl">
                    <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--surface-border)] bg-[var(--surface)]/50">
                         <div className="flex items-center gap-3">
                            <span className="w-2 h-2 rounded-full bg-indigo-500" />
                            <span className="text-sm font-bold text-[var(--foreground)] tracking-wider uppercase">Final Video Output</span>
                        </div>
                    </div>
                    <VideoPlayer 
                        src={job.video_url.startsWith('http') ? job.video_url : `${API_BASE_URL}${job.video_url}`}
                        className="w-full aspect-video rounded-none border-none"
                        autoPlay={true}
                    />
                </div>
            ) : (
                <LiveArtifactPreview 
                    plan={plan} 
                    storyboard={storyboard} 
                    status={job.status} 
                    renderProgress={renderProgress} 
                    thoughts={thoughts}
                />
            )}

                <SystemLogsSection thoughts={thoughts} agentBadgeColors={agentBadgeColors} />
        </div>
    );
}

function SystemLogsSection({ thoughts, agentBadgeColors }: { thoughts: any[], agentBadgeColors: Record<string, string> }) {
    const { settings } = useAppSettings();
    const [showThoughts, setShowThoughts] = useState(false);
    const thoughtsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (showThoughts) {
             thoughtsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [thoughts.length, showThoughts]);

    if (!settings.agentTransparency) return null;

    return (
        <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-lg group">
            <button 
                onClick={() => setShowThoughts(!showThoughts)}
                className="w-full flex items-center justify-between px-6 py-4 bg-[var(--surface)] group-hover:bg-[var(--background)]/50 transition-colors"
            >
                <div className="flex items-center gap-4">
                    <div className={`p-1.5 rounded-lg bg-[var(--background)] border border-[var(--surface-border)] transition-colors ${showThoughts ? 'text-indigo-500 border-indigo-500/30' : 'text-[var(--text-muted)]'}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <span className="text-sm font-bold text-[var(--foreground)] uppercase tracking-widest">System Logs</span>
                </div>
                <motion.svg 
                    animate={{ rotate: showThoughts ? 180 : 0 }}
                    className={`w-4 h-4 text-[var(--text-muted)] transition-colors duration-300 ${showThoughts ? 'text-indigo-500' : ''}`} 
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
            </button>
            
            <AnimatePresence>
                {showThoughts && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div
                            className="font-mono text-[13px] overflow-y-auto max-h-[250px] p-6 space-y-3 bg-neutral-950/50"
                            role="log"
                            aria-live="polite"
                        >
                            {thoughts.length === 0 && (
                                <p className="text-neutral-600 italic animate-pulse">Establishing secure connection to agents...</p>
                            )}
                            {thoughts.map((t, i) => (
                                <motion.div 
                                    key={i} 
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="flex gap-3 items-start"
                                >
                                    <span
                                        className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-tighter border ${agentBadgeColors[t.agent ?? ''] ?? 'bg-neutral-800 text-neutral-400 border-neutral-700'}`}
                                    >
                                        {t.agent ?? 'SYS'}
                                    </span>
                                    <span className="text-neutral-400 leading-relaxed break-words whitespace-pre-wrap">{t.content ?? ''}</span>
                                </motion.div>
                            ))}
                            <div ref={thoughtsEndRef} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
