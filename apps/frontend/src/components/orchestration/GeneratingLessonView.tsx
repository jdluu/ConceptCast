import React, { useMemo } from 'react';
import { JobStatus } from '@/lib/api/client';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { LessonArtifacts } from '@/components/orchestration/LessonArtifacts';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';

const AGENT_BADGE_COLORS: Record<string, string> = {
    analyst: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    validator: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    architect: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
    animator: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    reviewer: 'bg-pink-500/10 text-pink-500 border-pink-500/20',
    system: 'bg-[var(--surface-border)] text-[var(--text-muted)] border-[var(--surface-border)]',
};

const PIPELINE_STEPS = [
    { id: 'planning', label: 'Pedagogy', agent: 'Analyst' },
    { id: 'validating', label: 'Audit', agent: 'Critic' },
    { id: 'architecting', label: 'Visuals', agent: 'Architect' },
    { id: 'animating', label: 'Motion', agent: 'Animator' },
    { id: 'rendering', label: 'Synthesis', agent: 'Manim' },
];

interface GeneratingLessonViewProps {
    /** The current state and artifacts of the generation job. */
    job: JobStatus;
    /** The status of the Server-Sent Events (SSE) connection. */
    streamState: 'connecting' | 'connected' | 'error' | 'closed';
    /** Any error encountered during thought streaming. */
    streamError: Error | null;
}

/**
 * A simple animated spinner component.
 *
 * @param {Object} props - Component properties. 
 * @param {'sm' | 'md' | 'lg'} [props.size='md'] - The visual scale of the spinner.
 */
function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
    const sizeClasses = {
        sm: 'w-4 h-4 border-2',
        md: 'w-6 h-6 border-2',
        lg: 'w-10 h-10 border-3',
    };
    return (
        <div className={`${sizeClasses[size]} rounded-full border-[var(--surface-border)] border-t-indigo-500 animate-spin`} />
    );
}

/**
 * The primary view for observing an active lesson generation.
 *
 * This component visualizes the multi-agent orchestration by displaying
 * a live stream of agent thoughts, a pipeline progress indicator, and
 * real-time artifact previews (curriculum, storyboard, render progress).
 *
 * @param {GeneratingLessonViewProps} props - Component properties.
 * @returns {JSX.Element} The rendered generation view.
 */
export function GeneratingLessonView({ job, streamState, streamError }: GeneratingLessonViewProps) {
    const [isModalOpen, setIsModalOpen] = React.useState(false);

    /**
     * Groups raw thought logs into displayable blocks by agent and phase.
     * Prevents flickering and provides a more readable "conversational" stream.
     */
    const thoughts = useMemo(() => {
        const rawThoughts = job?.streamed_thoughts ?? [];
        const groups: Array<{ agent: string; phase: string; content: string }> = [];
        
        for (const t of rawThoughts) {
            const agent = t.agent ?? 'system';
            const phase = t.phase ?? 'output';
            const content = (t.content ?? '').trim();
            if (!content) continue;

            const last = groups[groups.length - 1];
            if (last && last.agent === agent && last.phase === phase) {
                const separator = (last.content.endsWith('.') || last.content.endsWith('!') || last.content.endsWith('?')) ? ' ' : ' ';
                last.content = (last.content + separator + content).replace(/\s+/g, ' ').trim();
            } else {
                groups.push({ agent, phase, content });
            }
        }
        return groups;
    }, [job?.streamed_thoughts]);

    if (streamError) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-8 bg-[var(--surface)] rounded-3xl border border-[var(--error-dim)]">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mb-6 border border-red-500/20">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                </div>
                <h2 className="text-2xl font-bold text-[var(--foreground)] mb-4">Connection Interrupted</h2>
                <p className="text-[var(--text-muted)] max-w-sm mb-8 leading-relaxed">The Council has disconnected or encountered a critical error while deliberating on your topic.</p>
                <div className="flex gap-4">
                     <button 
                        onClick={() => window.location.reload()}
                        className="px-8 py-3 bg-[var(--foreground)] text-[var(--background)] font-bold rounded-xl hover:opacity-90 transition-opacity uppercase tracking-widest text-xs"
                    >
                        Try Reconnecting
                    </button>
                </div>
            </div>
        );
    }

    if (!job || streamState === 'connecting') {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6">
                <LoadingSpinner size="lg" />
                <div className="text-center animate-pulse">
                    <p className="text-[var(--foreground)] font-bold tracking-widest uppercase text-xs mb-2">Summoning the Council</p>
                    <p className="text-[var(--text-muted)] text-[10px] italic">Synchronizing pedagogical nodes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
            {/* Header & Pipeline Progress */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 pb-8 border-b border-[var(--surface-border)]">
                <div className="space-y-2 text-center md:text-left">
                    <span className="text-[10px] font-bold text-indigo-500 uppercase tracking-[0.3em] mb-1 block">Live Generation</span>
                    <h1 className="text-4xl font-extrabold text-[var(--foreground)] tracking-tight leading-tight uppercase italic underline decoration-indigo-500 decoration-4 underline-offset-8">
                        {job.topic || 'Untitled Lesson'}
                    </h1>
                </div>

                <div className="flex items-center gap-1 sm:gap-3 bg-[var(--surface)] p-2 rounded-2xl border border-[var(--surface-border)] shadow-sm">
                    {PIPELINE_STEPS.map((step, idx) => {
                        const isCurrent = job.status === step.id;
                        const isPast = PIPELINE_STEPS.findIndex(s => s.id === job.status) > idx || job.status === 'completed';
                        
                        return (
                            <React.Fragment key={step.id}>
                                <div className="flex flex-col items-center group relative">
                                    <div className={`
                                        w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500
                                        ${isCurrent ? 'bg-indigo-500 border-indigo-500 text-white shadow-[0_0_20px_rgba(99,102,241,0.5)]' : 
                                          isPast ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-500' : 
                                          'bg-[var(--background)] border-[var(--surface-border)] text-[var(--text-muted)]'}
                                    `}>
                                        {isPast ? (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                        ) : (
                                            <span className="text-[10px] font-bold">{idx + 1}</span>
                                        )}
                                    </div>
                                    <div className="mt-2 text-center">
                                        <p className={`text-[9px] font-bold uppercase tracking-widest ${isCurrent ? 'text-indigo-500' : 'text-[var(--text-muted)]'}`}>
                                            {step.label}
                                        </p>
                                    </div>
                                    {/* Tooltip */}
                                    <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-[var(--foreground)] text-[var(--background)] text-[9px] font-bold uppercase tracking-widest px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap shadow-xl">
                                        {step.agent}
                                    </div>
                                </div>
                                {idx < PIPELINE_STEPS.length - 1 && (
                                    <div className={`w-4 sm:w-8 h-px mb-4 transition-colors duration-500 ${isPast ? 'bg-indigo-500/40' : 'bg-[var(--surface-border)]'}`} />
                                )}
                            </React.Fragment>
                        );
                    })}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                {/* Left: Deliberation Stream */}
                <div className="lg:col-span-5">
                    <CouncilDeliberation 
                        status={job.status} 
                        thoughts={thoughts} 
                        agentBadgeColors={AGENT_BADGE_COLORS} 
                    />
                </div>

                {/* Right: Artifact Preview */}
                <div className="lg:col-span-7">
                    <LessonArtifacts 
                        plan={job.plan ?? null} 
                        storyboard={job.storyboard ?? null} 
                        status={job.status}
                        renderProgress={job.render_progress || 0}
                        onViewFull={() => setIsModalOpen(true)}
                    />
                </div>
            </div>

             {/* Full Artifact Modal */}
             <LessonArtifactModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)}
                plan={job.plan ?? null}
                storyboard={job.storyboard ?? null}
             />
        </div>
    );
}
