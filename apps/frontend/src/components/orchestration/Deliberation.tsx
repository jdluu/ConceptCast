import { useRef, useEffect, useMemo } from 'react';
import { Activity } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Thought {
  agent: string;
  phase: string;
  content: string;
}

interface ThoughtBlock {
  agent: string;
  phase: string;
  content: string;
  startIndex: number;
}

export function CouncilDeliberation({ thoughts }: { thoughts: Thought[] }) {
  const logRef = useRef<HTMLDivElement>(null);

  // Group consecutive thoughts from the same agent and phase into "Blocks"
  // This prevents word-by-word flickering and makes it readable.
  const thoughtBlocks = useMemo(() => {
    if (thoughts.length === 0) return [];

    const blocks: ThoughtBlock[] = [];
    let currentBlock: ThoughtBlock | null = null;

    thoughts.forEach((t, i) => {
      if (!currentBlock || currentBlock.agent !== t.agent || currentBlock.phase !== t.phase) {
        currentBlock = {
          agent: t.agent,
          phase: t.phase,
          content: t.content,
          startIndex: i
        };
        blocks.push(currentBlock);
      } else {
        currentBlock.content += t.content;
      }
    });

    return blocks;
  }, [thoughts]);

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [thoughtBlocks.length]);

  return (
    <div className="overflow-hidden rounded-2xl border border-surface-border bg-terminal-bg shadow-2xl transition-all duration-500">
      {/* macOS Style Bar */}
      <div className="flex items-center justify-between border-b border-surface-border/30 bg-terminal-bg/80 px-4 py-2.5 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="h-2.5 w-2.5 rounded-full bg-macos-red/80 shadow-[0_0_8px_rgba(255,95,87,0.4)]" />
            <div className="h-2.5 w-2.5 rounded-full bg-macos-yellow/80 shadow-[0_0_8px_rgba(255,189,46,0.4)]" />
            <div className="h-2.5 w-2.5 rounded-full bg-macos-green/80 shadow-[0_0_8px_rgba(40,200,64,0.4)]" />
          </div>
          <div className="flex flex-col">
            <span className="font-mono text-[10px] font-bold tracking-[0.2em] text-terminal-text/60 uppercase">
              Protocol Terminal
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 font-mono text-[9px] font-medium tracking-wider text-terminal-text/30">
          <Activity className="h-3 w-3 text-council-active/50" />
          <span className="opacity-60">SESSION_LIVE:</span>
          <span className="text-terminal-text/50">council_stream.log</span>
        </div>
      </div>

      <div
        ref={logRef}
        className="custom-scrollbar max-h-[500px] min-h-[300px] space-y-2 overflow-y-auto p-6 font-mono text-xs leading-relaxed text-terminal-text"
        role="log"
      >
        {thoughtBlocks.length === 0 ? (
          <div className="flex h-full items-center justify-center opacity-20 italic py-20">
            Waiting for council transmission...
          </div>
        ) : (
          thoughtBlocks.map((block, i) => (
            <div key={i} className="group flex items-start gap-4 border-l-2 border-white/5 pl-4 transition-colors hover:border-council-active/30 py-1">
              <span className="shrink-0 text-terminal-text/20 text-[10px] mt-0.5">[{block.startIndex}]</span>
              <div className="flex flex-col gap-1 w-full">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'font-bold tracking-wider text-[10px]',
                      block.agent.toLowerCase().includes('pedagogue') ||
                        block.agent.toLowerCase().includes('analyst')
                        ? 'text-agent-planning'
                        : block.agent.toLowerCase().includes('critic') ||
                            block.agent.toLowerCase().includes('validator')
                          ? 'text-success'
                          : block.agent.toLowerCase().includes('architect')
                            ? 'text-agent-architecting'
                            : block.agent.toLowerCase().includes('animator')
                              ? 'text-agent-animating'
                              : 'text-agent-reviewing',
                    )}
                  >
                    [{block.agent.toUpperCase()}]
                  </span>
                  <span className="text-terminal-text/20 text-[9px] font-bold uppercase tracking-widest">
                    {block.phase}
                  </span>
                </div>
                <div className="text-terminal-text/90 break-words whitespace-pre-wrap">
                  {block.content}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
