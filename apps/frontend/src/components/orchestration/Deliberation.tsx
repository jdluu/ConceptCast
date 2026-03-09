import { useMemo, useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
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
  Activity,
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

const formatThought = (content: string) => {
  if (!content) return '';
  // Try to handle JSON-like tool calls by extracting the key/action
  if (content.startsWith('{') && content.includes(':')) {
    try {
      const parsed = JSON.parse(content);
      const keys = Object.keys(parsed);
      if (keys.length > 0) {
        return `Invoking ${keys[0]} to analyze logic...`;
      }
    } catch {
      if (content.includes('search_manim_docs')) return 'Searching Manim documentation...';
      if (content.includes('lint_manim_code')) return 'Linting Manim code...';
      if (content.includes('consult_critic')) return 'Consulting the Critic agent...';
    }
  }
  return content;
};

export function CouncilDeliberation({ status, thoughts, agentBadgeColors }: DeliberationProps) {
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const [showSystemLogs, setShowSystemLogs] = useState(false);

  // Map status to active agents for the dashboard view
  const activeAgents = useMemo(() => {
    if (status === 'planning' || status === 'validating' || status === 'planning_start')
      return ['analyst', 'validator'];
    if (status === 'architecting' || status === 'parallel_execution')
      return ['architect', 'validator'];
    if (status === 'animating' || status === 'animating_start' || status === 'rendering')
      return ['animator'];
    if (status === 'reviewing') return ['reviewer'];
    return [];
  }, [status]);

  return (
    <div className="space-y-6">
      <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] shadow-xl">
        <div className="flex items-center justify-between border-b border-[var(--surface-border)] bg-[var(--surface)]/50 px-6 py-4">
          <div className="flex items-center gap-3">
            <Users className="h-4 w-4 text-indigo-500" />
            <span className="text-[10px] font-bold tracking-[0.2em] text-[var(--foreground)] uppercase">
              Council Dashboard
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`h-1.5 w-1.5 rounded-full bg-emerald-500 ${prefersReducedMotion ? '' : 'animate-pulse'}`}
            />
            <span className="text-[9px] font-bold tracking-widest text-emerald-500/80 uppercase italic">
              Council Active
            </span>
          </div>
        </div>
        <div className="p-6">
          <CouncilStatusBoard
            activeAgents={activeAgents}
            thoughts={thoughts}
            agentBadgeColors={agentBadgeColors}
            prefersReducedMotion={prefersReducedMotion}
          />
        </div>
      </div>

      <SystemLogsToggle
        show={showSystemLogs}
        onToggle={() => setShowSystemLogs(!showSystemLogs)}
        thoughts={thoughts}
        agentBadgeColors={agentBadgeColors}
        prefersReducedMotion={prefersReducedMotion}
      />
    </div>
  );
}

function CouncilStatusBoard({
  activeAgents,
  thoughts,
  agentBadgeColors,
  prefersReducedMotion,
}: {
  activeAgents: string[];
  thoughts: Thought[];
  agentBadgeColors: Record<string, string>;
  prefersReducedMotion: boolean;
}) {
  const agents = [
    { id: 'analyst', label: 'Pedagogue', icon: <Search className="h-4 w-4" /> },
    { id: 'validator', label: 'Critic', icon: <CheckCircle className="h-4 w-4" /> },
    { id: 'architect', label: 'Architect', icon: <Layout className="h-4 w-4" /> },
    { id: 'animator', label: 'Animator', icon: <Play className="h-4 w-4" /> },
    { id: 'reviewer', label: 'Reviewer', icon: <Zap className="h-4 w-4" /> },
  ];

  const activeCardRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the active agent card when activeAgents change or thoughts update
  useEffect(() => {
    if (activeCardRef.current) {
      activeCardRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [activeAgents, thoughts.length]);

  return (
    <div className="custom-scrollbar grid max-h-[600px] grid-cols-1 gap-4 overflow-y-auto pr-2">
      {agents.map((agent) => {
        const isActive = activeAgents.includes(agent.id);
        // Get most recent thought for this agent
        const latestThought = thoughts.toReversed().find((t) => t.agent === agent.id);

        return (
          <motion.div
            key={agent.id}
            ref={isActive ? activeCardRef : null}
            initial={false}
            animate={{
              opacity: isActive ? 1 : 0.4,
              scale: isActive ? 1 : 0.98,
              borderColor: isActive ? 'rgba(99, 102, 241, 0.3)' : 'var(--surface-border)',
            }}
            className={`rounded-xl border bg-[var(--background)]/40 p-4 transition-all ${isActive ? 'shadow-md ring-1 shadow-indigo-500/5 ring-indigo-500/20' : ''}`}
          >
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`rounded-lg p-2 ${isActive ? 'bg-indigo-500/10 text-indigo-500' : 'bg-[var(--surface-border)] text-[var(--text-muted)]'}`}
                >
                  {agent.icon}
                </div>
                <div>
                  <h4
                    className={`text-[10px] font-bold tracking-widest uppercase ${isActive ? 'text-[var(--foreground)]' : 'text-[var(--text-muted)]'}`}
                  >
                    {agent.label}
                  </h4>
                  <span
                    className={`rounded px-1 font-mono text-[8px] uppercase ${agentBadgeColors[agent.id] || 'bg-[var(--surface)] opacity-50'}`}
                  >
                    {agent.id}
                  </span>
                </div>
              </div>
              {isActive && (
                <span className="flex items-center gap-1.5">
                  <Activity
                    className={`h-3 w-3 text-indigo-500 ${prefersReducedMotion ? '' : 'animate-pulse'}`}
                  />
                  <span className="text-[9px] font-bold tracking-tighter text-indigo-500 uppercase">
                    Processing
                  </span>
                </span>
              )}
            </div>

            <div
              className={`text-xs leading-relaxed ${isActive ? 'text-[var(--text-muted)]' : 'line-clamp-2 text-[var(--text-muted)] italic opacity-50'}`}
            >
              {latestThought
                ? formatThought(latestThought.content)
                : isActive
                  ? 'Initiating reasoning...'
                  : 'Waiting for objective...'}
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
  agentBadgeColors,
  prefersReducedMotion,
}: {
  show: boolean;
  onToggle: () => void;
  thoughts: Thought[];
  agentBadgeColors: Record<string, string>;
  prefersReducedMotion: boolean;
}) {
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (show && logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [show, thoughts.length]);

  return (
    <div className="group overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] shadow-sm">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between bg-[var(--surface)] px-6 py-4 transition-colors hover:bg-[var(--background)]/50"
      >
        <div className="flex items-center gap-4">
          <div
            className={`rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-1.5 transition-colors ${show ? 'border-indigo-500/30 text-indigo-500' : 'text-[var(--text-muted)]'}`}
          >
            <Terminal className="h-4 w-4" />
          </div>
          <span className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">
            Full Session Protocol
          </span>
        </div>
        <motion.div animate={prefersReducedMotion ? {} : { rotate: show ? 180 : 0 }}>
          <ChevronDown
            className={`h-4 w-4 text-[var(--text-muted)] ${show ? 'text-indigo-500' : ''}`}
          />
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
              className="custom-scrollbar max-h-[400px] space-y-3 overflow-y-auto border-t border-[var(--surface-border)] bg-[var(--background)]/30 p-6 font-mono text-[11px]"
              role="log"
            >
              {thoughts.length === 0 ? (
                <p className="py-4 text-center text-[var(--text-muted)] italic">
                  Logs pending generation...
                </p>
              ) : (
                thoughts.map((t, i) => (
                  <div
                    key={i}
                    className="ml-1 flex items-start gap-3 border-l border-[var(--surface-border)] pl-3"
                  >
                    <div className="flex min-w-[70px] flex-col gap-1">
                      <span
                        className={`shrink-0 rounded border px-1.5 py-0.5 text-[8px] font-bold ${agentBadgeColors[t.agent] ?? 'border-[var(--surface-border)] bg-[var(--surface)] text-[var(--text-muted)]'}`}
                      >
                        {t.agent.toUpperCase()}
                      </span>
                      <span className="text-[8px] text-[var(--text-muted)] uppercase opacity-50">
                        {t.phase}
                      </span>
                    </div>
                    <span className="max-w-full truncate break-words whitespace-pre-wrap text-[var(--foreground)] opacity-80">
                      {t.content}
                    </span>
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
