import { useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { 
    Users, 
    Zap, 
    Search, 
    Layout, 
    Play, 
    CheckCircle, 
    Terminal,
    ChevronDown,
    Activity
} from 'lucide-react';

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
    
    // Map status to active agents for the dashboard view
    const activeAgents = useMemo(() => {
        if (status === 'planning' || status === 'validating') return ['analyst', 'validator'];
        if (status === 'architecting') return ['architect'];
        if (status === 'animating' || status === 'rendering') return ['animator'];
        if (status === 'reviewing') return ['reviewer'];
        return [];
    }, [status]);

    return (
        <div className="space-y-6">
            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-xl">
                <div className="px-6 py-4 border-b border-[var(--surface-border)] bg-[var(--surface)]/50 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Users className="w-4 h-4 text-indigo-500" />
                        <span className="text-[10px] font-bold text-[var(--foreground)] uppercase tracking-[0.2em]">Council Dashboard</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[9px] font-bold text-emerald-500/80 uppercase tracking-widest italic">Council Active</span>
                    </div>
                </div>
                <div className="p-6">
                    <CouncilStatusBoard 
                        activeAgents={activeAgents} 
                        thoughts={thoughts} 
                        agentBadgeColors={agentBadgeColors} 
                    />
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

function CouncilStatusBoard({ 
    activeAgents, 
    thoughts, 
    agentBadgeColors 
}: { 
    activeAgents: string[], 
    thoughts: Thought[], 
    agentBadgeColors: Record<string, string> 
}) {
    const agents = [
        { id: 'analyst', label: 'Pedagogue', icon: <Search className="w-4 h-4" /> },
        { id: 'validator', label: 'Critic', icon: <CheckCircle className="w-4 h-4" /> },
        { id: 'architect', label: 'Architect', icon: <Layout className="w-4 h-4" /> },
        { id: 'animator', label: 'Animator', icon: <Play className="w-4 h-4" /> },
        { id: 'reviewer', label: 'Reviewer', icon: <Zap className="w-4 h-4" /> }
    ];

    return (
        <div className="grid grid-cols-1 gap-4">
            {agents.map((agent) => {
                const isActive = activeAgents.includes(agent.id);
                // Get most recent thought for this agent
                const latestThought = [...thoughts].reverse().find(t => t.agent === agent.id);
                
                return (
                    <motion.div 
                        key={agent.id}
                        initial={false}
                        animate={{ 
                            opacity: isActive ? 1 : 0.4,
                            scale: isActive ? 1 : 0.98,
                            borderColor: isActive ? 'rgba(99, 102, 241, 0.3)' : 'var(--surface-border)'
                        }}
                        className={`p-4 rounded-xl border bg-[var(--background)]/40 transition-all ${isActive ? 'shadow-md shadow-indigo-500/5' : ''}`}
                    >
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${isActive ? 'bg-indigo-500/10 text-indigo-500' : 'bg-[var(--surface-border)] text-[var(--text-muted)]'}`}>
                                    {agent.icon}
                                </div>
                                <div>
                                    <h4 className={`text-[10px] font-bold uppercase tracking-widest ${isActive ? 'text-[var(--foreground)]' : 'text-[var(--text-muted)]'}`}>
                                        {agent.label}
                                    </h4>
                                    <span className={`text-[8px] font-mono px-1 rounded uppercase ${agentBadgeColors[agent.id] || 'bg-[var(--surface)] opacity-50'}`}>
                                        {agent.id}
                                    </span>
                                </div>
                            </div>
                            {isActive && (
                                <span className="flex items-center gap-1.5">
                                    <Activity className="w-3 h-3 text-indigo-500 animate-pulse" />
                                    <span className="text-[9px] font-bold text-indigo-500 uppercase tracking-tighter">Processing</span>
                                </span>
                            )}
                        </div>

                        <div className={`text-xs leading-relaxed ${isActive ? 'text-[var(--text-muted)]' : 'text-[var(--text-muted)] opacity-50 italic line-clamp-1'}`}>
                            {latestThought ? latestThought.content : (isActive ? 'Initiating reasoning...' : 'Waiting for objective...')}
                        </div>
                    </motion.div>
                );
            })}
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

    return (
        <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-sm group">
            <button 
                onClick={onToggle}
                className="w-full flex items-center justify-between px-6 py-4 bg-[var(--surface)] hover:bg-[var(--background)]/50 transition-colors"
            >
                <div className="flex items-center gap-4">
                    <div className={`p-1.5 rounded-lg bg-[var(--background)] border border-[var(--surface-border)] transition-colors ${show ? 'text-indigo-500 border-indigo-500/30' : 'text-[var(--text-muted)]'}`}>
                        <Terminal className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest">Full Session Protocol</span>
                </div>
                <motion.div animate={{ rotate: show ? 180 : 0 }}>
                    <ChevronDown className={`w-4 h-4 text-[var(--text-muted)] ${show ? 'text-indigo-500' : ''}`} />
                </motion.div>
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
                            className="font-mono text-[11px] overflow-y-auto max-h-[400px] p-6 space-y-3 bg-[var(--background)]/30 border-t border-[var(--surface-border)] custom-scrollbar"
                            role="log"
                        >
                            {thoughts.length === 0 ? (
                                <p className="text-[var(--text-muted)] italic text-center py-4">Logs pending generation...</p>
                            ) : (
                                thoughts.map((t, i) => (
                                    <div key={i} className="flex gap-3 items-start border-l border-[var(--surface-border)] pl-3 ml-1">
                                        <div className="flex flex-col gap-1 min-w-[70px]">
                                            <span className={`shrink-0 px-1.5 py-0.5 rounded text-[8px] font-bold border ${agentBadgeColors[t.agent] ?? 'bg-[var(--surface)] text-[var(--text-muted)] border-[var(--surface-border)]'}`}>
                                                {t.agent.toUpperCase()}
                                            </span>
                                            <span className="text-[8px] text-[var(--text-muted)] opacity-50 uppercase">{t.phase}</span>
                                        </div>
                                        <span className="text-[var(--foreground)] opacity-80 break-words whitespace-pre-wrap">{t.content}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
