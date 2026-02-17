import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppSettings } from '@/lib/contexts/appSettings';

interface Thought {
    agent: string;
    phase: string;
    content: string;
}

interface DeliberationProps {
    status: string;
    thoughts: Thought[];
    agentBadgeColors: Record<string, string>;
}

export function CouncilDeliberation({ 
    status, 
    thoughts, 
    agentBadgeColors 
}: DeliberationProps) {
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

function LiveActivityStream({ thoughts, agentBadgeColors }: { thoughts: Thought[], agentBadgeColors: Record<string, string> }) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
        }
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
    thoughts: Thought[];
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
