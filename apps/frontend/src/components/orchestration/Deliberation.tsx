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
          startIndex: i,
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
    <div className="border-surface-border bg-terminal-bg overflow-hidden rounded-2xl border shadow-2xl transition-all duration-500">
      {/* macOS Style Bar */}
      <div className="border-surface-border/30 bg-terminal-bg/80 flex items-center justify-between border-b px-4 py-2.5 backdrop-blur-md">
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="bg-macos-red/80 h-2.5 w-2.5 rounded-full shadow-[0_0_8px_rgba(255,95,87,0.4)]" />
            <div className="bg-macos-yellow/80 h-2.5 w-2.5 rounded-full shadow-[0_0_8px_rgba(255,189,46,0.4)]" />
            <div className="bg-macos-green/80 h-2.5 w-2.5 rounded-full shadow-[0_0_8px_rgba(40,200,64,0.4)]" />
          </div>
          <div className="flex flex-col">
            <span className="text-terminal-text/60 font-mono text-[10px] font-bold tracking-[0.2em] uppercase">
              Protocol Terminal
            </span>
          </div>
        </div>
        <div className="text-terminal-text/30 flex items-center gap-2 font-mono text-[9px] font-medium tracking-wider">
          <Activity className="text-council-active/50 h-3 w-3" />
          <span className="opacity-60">SESSION_LIVE:</span>
          <span className="text-terminal-text/50">council_stream.log</span>
        </div>
      </div>

      <div
        ref={logRef}
        className="custom-scrollbar text-terminal-text max-h-[500px] min-h-[300px] space-y-2 overflow-y-auto p-6 font-mono text-xs leading-relaxed"
        role="log"
      >
        {thoughtBlocks.length === 0 ? (
          <div className="flex h-full items-center justify-center py-20 italic opacity-20">
            Waiting for council transmission...
          </div>
        ) : (
          thoughtBlocks.map((block) => (
            <div
              key={`${block.agent}:${block.phase}:${block.startIndex}`}
              className="group hover:border-council-active/30 flex items-start gap-4 border-l-2 border-white/5 py-1 pl-4 transition-colors"
            >
              <span className="text-terminal-text/20 mt-0.5 shrink-0 text-[10px]">
                [{block.startIndex}]
              </span>
              <div className="flex w-full flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'text-[10px] font-bold tracking-wider',
                      block.agent.toLowerCase().includes('planner') ||
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
                  <span className="text-terminal-text/20 text-[9px] font-bold tracking-widest uppercase">
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
