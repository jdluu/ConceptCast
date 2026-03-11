import { useRef, useEffect } from 'react';
import { Activity } from 'lucide-react';

interface Thought {
  agent: string;
  phase: string;
  content: string;
}


export function CouncilDeliberation({ thoughts }: { thoughts: Thought[] }) {
  return (
    <div className="w-full">
      <SystemLogs thoughts={thoughts} />
    </div>
  );
}

function SystemLogs({
  thoughts,
}: {
  thoughts: Thought[];
}) {
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [thoughts.length]);

  return (
    <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--terminal-bg)] shadow-2xl transition-all duration-500">
      {/* macOS Style Bar */}
      <div className="flex items-center justify-between border-b border-[var(--surface-border)]/30 bg-[var(--terminal-bg)]/80 px-4 py-2 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
            <div className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
          </div>
          <span className="ml-2 font-mono text-[9px] font-bold tracking-widest text-[var(--terminal-text)]/50 uppercase">
            Protocol Terminal
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[8px] text-[var(--terminal-text)]/30">
          <Activity className="h-2.5 w-2.5 animate-pulse" />
          <span>council_stream.log</span>
        </div>
      </div>

      <div
        ref={logRef}
        className="custom-scrollbar max-h-[400px] min-h-[240px] space-y-1.5 overflow-y-auto p-4 font-mono text-[10px] leading-relaxed text-[var(--terminal-text)]"
        role="log"
      >
        {thoughts.length === 0 ? (
          <div className="flex h-full items-center justify-center py-20 text-[var(--terminal-text)]/30">
            <span className="animate-pulse">Waiting for session initialization...</span>
          </div>
        ) : (
          thoughts.map((t, i) => (
            <div key={i} className="group flex gap-2.5 transition-opacity">
              <span className="shrink-0 text-[var(--terminal-text)]/20">
                {new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <div className="flex gap-1.5">
                <span
                  className={`font-bold ${
                    t.agent.toLowerCase().includes('pedagogue') || t.agent.toLowerCase().includes('analyst')
                      ? 'text-blue-400'
                      : t.agent.toLowerCase().includes('critic') || t.agent.toLowerCase().includes('validator')
                        ? 'text-emerald-400'
                        : t.agent.toLowerCase().includes('architect')
                          ? 'text-purple-400'
                          : t.agent.toLowerCase().includes('animator')
                            ? 'text-orange-400'
                            : 'text-pink-400'
                  }`}
                >
                  [{t.agent.toUpperCase()}]
                </span>
                <span className="text-[var(--terminal-text)]/40">{'->'}</span>
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
