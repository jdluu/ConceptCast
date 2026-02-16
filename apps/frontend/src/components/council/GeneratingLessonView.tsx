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
    analyst: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20',
    validator: 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20',
    architect: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-yellow-500/20',
    animator: 'bg-orange-500/10 text-orange-700 dark:text-orange-300 border-orange-500/20',
    reviewer: 'bg-teal-500/10 text-teal-700 dark:text-teal-300 border-teal-500/20',
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
}


function LiveArtifactPreview({ plan, storyboard, status, renderProgress }: LiveArtifactPreviewProps) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const isRendering = status === 'rendering';
    const hasStoryboard = !!storyboard;
    const hasPlan = !!plan;

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

                <div className="p-6 overflow-y-auto custom-scrollbar">
                    <AnimatePresence mode="wait">
                        {/* 1. Show Storyboard if it exists */}
                        {hasStoryboard ? (
                            <motion.div 
                                key="storyboard"
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
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
                        ) : hasPlan ? (
                            /* 2. Show Plan if it exists */
                            <motion.div 
                                key="plan"
                                initial={{ opacity: 0, scale: 0.98 }}
                                animate={{ opacity: 1, scale: 1 }}
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
                        ) : (
                            /* 3. Loading state */
                            <motion.div 
                                key="loading"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] space-y-4 py-24"
                            >
                                <div className="w-10 h-10 rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 animate-spin shadow-sm" />
                                <p className="text-sm font-medium italic opacity-60">Connecting to Council...</p>
                            </motion.div>
                        )}
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
                                    <h3 className="text-lg font-bold text-[var(--foreground)]">{scene.title}</h3>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--surface-border)]">
                                        <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-2">Visual Composition</div>
                                        <p className="text-[var(--text-muted)] text-sm leading-relaxed">{scene.description}</p>
                                    </div>
                                    <div className="p-4 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                                        <div className="text-[10px] font-bold text-indigo-500 dark:text-indigo-300 uppercase tracking-widest mb-2">Narration Script</div>
                                        <p className="text-sm italic text-[var(--foreground)]">"{scene.narration}"</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : hasPlan ? (
                    <div className="space-y-6">
                        <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-8">
                             <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-1">Target Audience</div>
                             <p className="text-[var(--foreground)] text-lg font-bold">{plan!.target_audience}</p>
                        </div>
                        {plan!.teaching_steps.map((step) => (
                            <div key={step.step_id} className="flex gap-6 p-4 rounded-xl hover:bg-[var(--background)]/40 transition-colors">
                                <div className="shrink-0 w-10 h-10 rounded-full bg-[var(--background)] flex items-center justify-center text-[var(--foreground)] font-bold border border-[var(--surface-border)]">
                                    {step.step_id}
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold text-[var(--foreground)]">{step.concept}</h3>
                                    <div className="flex flex-col gap-1">
                                         <p className="text-sm text-[var(--text-muted)] leading-relaxed"><span className="text-indigo-500 font-semibold italic">Metaphor:</span> {step.visual_metaphor}</p>
                                         <p className="text-sm text-[var(--text-muted)] mt-2 p-3 bg-[var(--background)]/50 rounded-lg border border-[var(--surface-border)] whitespace-pre-wrap"><span className="text-[10px] font-bold block mb-1 text-indigo-500 opacity-60">NARRATION</span>"{step.narration}"</p>
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
                            <div className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] opacity-60">
                                <span className="w-1 h-1 rounded-full bg-[var(--surface-border)]" />
                                {job.provider && (
                                    <span className="flex items-center gap-1.5 text-indigo-500">
                                        {job.provider}
                                        {job.model_id && <span className="text-[var(--text-muted)] lowercase font-medium">({job.model_id})</span>}
                                    </span>
                                )}
                                {job.provider && job.target_audience && <span className="w-1 h-1 rounded-full bg-[var(--surface-border)]" />}
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
                <div className="space-y-8">
                    <LiveArtifactPreview 
                        plan={plan} 
                        storyboard={storyboard} 
                        status={job.status} 
                        renderProgress={renderProgress} 
                    />
                    <CouncilDeliberation 
                        status={job.status}
                        thoughts={thoughts} 
                        agentBadgeColors={agentBadgeColors} 
                    />
                </div>
            )}
        </div>
    );
}

function CouncilDeliberation({ 
    status, 
    thoughts, 
    agentBadgeColors 
}: { 
    status: string;
    thoughts: any[]; 
    agentBadgeColors: Record<string, string> 
}) {
    const { settings } = useAppSettings();
    const [showSystemLogs, setShowSystemLogs] = useState(false);
    
    const relevantThoughts = useMemo(() => {
        if (status === 'architecting') return thoughts.filter(t => t.agent === 'architect');
        if (status === 'planning' || status === 'validating') return thoughts.filter(t => t.agent === 'analyst' || t.agent === 'validator');
        if (status === 'animating' || status === 'rendering' || status === 'reviewing') return thoughts.filter(t => t.agent === 'animator' || t.agent === 'reviewer');
        return [];
    }, [status, thoughts]);

    return (
        <div className="space-y-6">
            {/* Live Activity Feed */}
            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-lg">
                <div className="px-6 py-4 border-b border-[var(--surface-border)] bg-[var(--surface)]/50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse" />
                        <span className="text-[10px] font-bold text-[var(--foreground)] uppercase tracking-[0.2em]">Council Deliberation</span>
                    </div>
                    <span className="text-[9px] font-bold text-indigo-500/60 uppercase tracking-widest italic">Live Feedback</span>
                </div>
                <div className="p-6">
                    <LiveActivityStream thoughts={relevantThoughts} agentBadgeColors={agentBadgeColors} />
                </div>
            </div>

            {/* System Logs (Audit Trail) */}
            {settings.agentTransparency && (
                <SystemLogsToggle 
                    show={showSystemLogs} 
                    onToggle={() => setShowSystemLogs(!showSystemLogs)} 
                    thoughts={thoughts}
                    agentBadgeColors={agentBadgeColors}
                />
            )}
        </div>
    );
}

function LiveActivityStream({ thoughts, agentBadgeColors }: { thoughts: any[], agentBadgeColors: Record<string, string> }) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }, [thoughts.length]);

    if (thoughts.length === 0) {
        return (
            <div className="py-8 flex flex-col items-center justify-center text-[var(--text-muted)] space-y-3">
                <div className="w-6 h-6 rounded-full border border-[var(--surface-border)] border-t-indigo-500/50 animate-spin" />
                <p className="text-xs font-medium italic">Agents are deliberating...</p>
            </div>
        );
    }

    return (
        <div 
            ref={scrollRef}
            className="max-h-[200px] overflow-y-auto custom-scrollbar space-y-4 pr-2"
        >
            {thoughts.map((t, i) => (
                <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex gap-4 items-start"
                >
                    <div className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${agentBadgeColors[t.agent]}`}>
                        {t.agent}
                    </div>
                    <p className="text-[var(--foreground)] text-[13px] leading-relaxed opacity-80">{t.content}</p>
                </motion.div>
            ))}
        </div>
    );
}

function SystemLogsToggle({ 
    show, 
    onToggle, 
    thoughts, 
    agentBadgeColors 
}: { 
    show: boolean; 
    onToggle: () => void; 
    thoughts: any[];
    agentBadgeColors: Record<string, string>;
}) {
    const logRef = useRef<HTMLDivElement>(null);
    const [isAtBottom, setIsAtBottom] = useState(true);

    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const target = e.currentTarget;
        const bottom = Math.abs(target.scrollHeight - target.clientHeight - target.scrollTop) < 50;
        setIsAtBottom(bottom);
    };

    useEffect(() => {
        if (show && isAtBottom) {
             logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
        }
    }, [thoughts.length, show, isAtBottom]);

    return (
        <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-sm group">
            <button 
                onClick={onToggle}
                className="w-full flex items-center justify-between px-6 py-4 bg-[var(--surface)] hover:bg-[var(--background)]/50 transition-colors"
            >
                <div className="flex items-center gap-4">
                    <div className={`p-1.5 rounded-lg bg-[var(--background)] border border-[var(--surface-border)] transition-colors ${show ? 'text-indigo-500 border-indigo-500/30' : 'text-[var(--text-muted)]'}`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                    </div>
                    <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest">Full Session Logs</span>
                </div>
                <motion.svg 
                    animate={{ rotate: show ? 180 : 0 }}
                    className={`w-4 h-4 text-[var(--text-muted)] ${show ? 'text-indigo-500' : ''}`} 
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </motion.svg>
            </button>
            
            <AnimatePresence>
                {show && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                    >
                        <div
                            ref={logRef}
                            onScroll={handleScroll}
                            className="font-mono text-[12px] overflow-y-auto max-h-[300px] p-6 space-y-3 bg-[var(--background)]/30 border-t border-[var(--surface-border)]"
                            role="log"
                        >
                            {thoughts.map((t, i) => (
                                <div key={i} className="flex gap-3 items-start opacity-60">
                                    <span className={`shrink-0 px-1.5 py-0.5 rounded text-[9px] font-bold border ${agentBadgeColors[t.agent] ?? 'bg-[var(--surface)] text-[var(--text-muted)] border-[var(--surface-border)]'}`}>
                                        {t.agent ?? 'SYS'}
                                    </span>
                                    <span className="text-[var(--foreground)] break-words whitespace-pre-wrap">{t.content ?? ''}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
