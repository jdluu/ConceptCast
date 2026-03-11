import { useRef, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Thought {
  agent: string;
  phase: string;
  content: string;
}


export function CouncilDeliberation({ thoughts }: { thoughts: Thought[] }) {
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [thoughts.length]);

  return (
    <div className="overflow-hidden rounded-2xl border border-surface-border bg-terminal-bg shadow-2xl transition-all duration-500">
      {/* macOS Style Bar */}
      <div className="flex items-center justify-between border-b border-surface-border/30 bg-terminal-bg/80 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-macos-red/80 shadow-sm" />
            <div className="h-2.5 w-2.5 rounded-full bg-macos-yellow/80 shadow-sm" />
            <div className="h-2.5 w-2.5 rounded-full bg-macos-green/80 shadow-sm" />
          </div>
          <span className="ml-2 font-mono text-micro font-bold tracking-widest text-terminal-text/50 uppercase">
            Protocol Terminal
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-nano text-terminal-text/30">
          <Activity className="h-2.5 w-2.5 animate-pulse" />
          <span>council_stream.log</span>
        </div>
      </div>

      <div
        ref={logRef}
        className="custom-scrollbar max-h-md min-h-sm space-y-1.5 overflow-y-auto p-4 font-mono text-tiny leading-relaxed text-terminal-text"
        role="log"
      >
        {thoughts.length === 0 ? (
          <div className="flex h-full items-center justify-center opacity-20 italic">
            Waiting for council transmission...
          </div>
        ) : (
          thoughts.map((t, i) => (
            <div key={i} className="group flex items-start gap-3 border-l border-white/5 pl-2 transition-colors hover:border-white/20">
              <span className="shrink-0 text-terminal-text/20">[{i}]</span>
              <div className="flex flex-wrap gap-1.5">
                <span
                  className={cn(
                    'font-bold',
                    t.agent.toLowerCase().includes('pedagogue') ||
                      t.agent.toLowerCase().includes('analyst')
                      ? 'text-agent-planning'
                      : t.agent.toLowerCase().includes('critic') ||
                          t.agent.toLowerCase().includes('validator')
                        ? 'text-success'
                        : t.agent.toLowerCase().includes('architect')
                          ? 'text-agent-architecting'
                          : t.agent.toLowerCase().includes('animator')
                            ? 'text-agent-animating'
                            : 'text-agent-reviewing',
                  )}
                >
                  [{t.agent.toUpperCase()}]
                </span>
                <span className="text-terminal-text/40">{'->'}</span>
                <span className="break-words opacity-90 transition-opacity group-hover:opacity-100">
                  {t.content}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
