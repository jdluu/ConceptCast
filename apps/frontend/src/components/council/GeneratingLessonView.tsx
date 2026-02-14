import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { JobStatus, Storyboard, CurriculumPlan } from '../../lib/api';
import { useJobStore } from '../../lib/store/useJobStore';
import { PipelineSteps } from '../ui/PipelineSteps';

const agentBadgeColors: Record<string, string> = {
    analyst: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
    validator: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
    architect: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40',
    animator: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
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
                <span className="flex items-center gap-1.5 text-sm text-neutral-400">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" aria-hidden />
                    Connecting…
                </span>
            )}
            {state === 'connected' && (
                <span className="flex items-center gap-1.5 text-sm text-emerald-400">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" aria-hidden />
                    Live
                </span>
            )}
            {state === 'error' && (
                <span className="flex items-center gap-1.5 text-sm text-amber-400">
                    <span className="w-2 h-2 rounded-full bg-amber-400" aria-hidden />
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
}

function LiveArtifactPreview({ plan, storyboard, status, renderProgress }: LiveArtifactPreviewProps) {
    const isRendering = status === 'rendering';
    const hasStoryboard = !!storyboard;
    const hasPlan = !!plan;

    return (
        <motion.div 
            layout
            className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-2xl"
        >
            <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-neutral-900/50">
                <div className="flex items-center gap-2">
                    <motion.span 
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-2 h-2 rounded-full bg-indigo-500" 
                    />
                    <span className="text-sm font-semibold text-white tracking-wide uppercase">
                        {isRendering ? 'Rendering Preview' : hasStoryboard ? 'Visual Storyboard' : 'Curriculum Plan'}
                    </span>
                </div>
                {isRendering && (
                    <span className="text-xs font-mono text-indigo-400">
                        {Math.round(renderProgress)}% COMPLETE
                    </span>
                )}
            </div>

            <div className="p-6 min-h-[300px] max-h-[500px] overflow-y-auto custom-scrollbar">
                <AnimatePresence mode="wait">
                    {!hasPlan && !hasStoryboard ? (
                        <motion.div 
                            key="loading"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="h-full flex flex-col items-center justify-center text-neutral-600 space-y-3 py-20"
                        >
                            <div className="w-8 h-8 rounded-full border-2 border-neutral-800 border-t-neutral-600 animate-spin" />
                            <p className="text-sm font-medium italic">Agents are assembling the framework...</p>
                        </motion.div>
                    ) : (hasStoryboard ? (
                        <motion.div 
                            key="storyboard"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            {storyboard.scenes.map((scene) => (
                                <div key={scene.scene_id} className="group relative pl-6 border-l-2 border-neutral-800 hover:border-indigo-500 transition-colors">
                                    <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-neutral-800 group-hover:bg-indigo-500 transition-colors" />
                                    <div className="text-[10px] font-bold text-neutral-500 uppercase tracking-widest mb-1">Scene {scene.scene_id}</div>
                                    <h3 className="text-white font-semibold text-lg mb-2">{scene.title}</h3>
                                    <p className="text-neutral-400 text-sm leading-relaxed">{scene.description}</p>
                                </div>
                            ))}
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="plan"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-6"
                        >
                            {plan!.teaching_steps.map((step) => (
                                <div key={step.step_id} className="group flex gap-4">
                                    <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-sm">
                                        {step.step_id}
                                    </span>
                                    <div>
                                        <h3 className="text-white font-medium mb-1">{step.concept}</h3>
                                        <p className="text-neutral-500 text-sm">
                                            <span className="text-indigo-400/60 font-medium">Metaphor:</span> {step.visual_metaphor}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}

interface GeneratingLessonViewProps {
    streamState?: StreamState;
    streamError?: Error | null;
}

export function GeneratingLessonView({
    streamState = 'closed',
    streamError = null,
}: GeneratingLessonViewProps) {
    const { currentJob: job, submittedTopic: topic, renderProgress } = useJobStore();
    const [showThoughts, setShowThoughts] = useState(false);

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
    const thoughtsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        thoughtsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [rawThoughts.length]);

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="flex items-center justify-between gap-4">
                <div className="space-y-1">
                    <h1 className="text-2xl font-bold text-white tracking-tight">
                        {topic || 'Untitled Concept'}
                    </h1>
                    <div className="flex items-center gap-2 text-sm text-neutral-500">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                        {currentLabel}
                    </div>
                </div>
                <StreamIndicator state={streamState} error={streamError} />
            </header>

            <div className="bg-neutral-900/40 border border-neutral-800/60 rounded-2xl p-8 backdrop-blur-sm">
                <PipelineSteps status={job.status} />
            </div>

            <LiveArtifactPreview 
                plan={plan} 
                storyboard={storyboard} 
                status={job.status} 
                renderProgress={renderProgress} 
            />

            <div className="bg-neutral-900/80 border border-neutral-800 rounded-xl overflow-hidden shadow-lg group">
                <button 
                    onClick={() => setShowThoughts(!showThoughts)}
                    className="w-full flex items-center justify-between px-4 py-3 bg-neutral-900 group-hover:bg-neutral-800/50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className={`p-1 rounded-md bg-neutral-800 transition-colors ${showThoughts ? 'text-indigo-400' : 'text-neutral-500'}`}>
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <span className="text-sm font-semibold text-neutral-300 uppercase tracking-wider">System Logs</span>
                    </div>
                    <motion.svg 
                        animate={{ rotate: showThoughts ? 180 : 0 }}
                        className={`w-4 h-4 text-neutral-500 transition-colors duration-300 ${showThoughts ? 'text-indigo-400' : ''}`} 
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
        </div>
    );
}
