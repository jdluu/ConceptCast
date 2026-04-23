import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Search, Layout, Terminal } from 'lucide-react';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';

interface CollapsibleState {
  blueprint: boolean;
  storyboard: boolean;
  terminal: boolean;
}

interface StreamedThought {
  agent: string;
  phase: string;
  content: string;
  ts: string;
}

interface ArtifactSectionsProps {
  plan: CurriculumPlan | null;
  storyboard: Storyboard | null;
  status: string;
  thoughts: StreamedThought[];
  onViewFullPlan: () => void;
}

/**
 * Renders the three collapsible artifact panels: Curriculum Plan,
 * Visual Storyboard, and Council Stream (thoughts terminal).
 */
export function ArtifactSections({
  plan,
  storyboard,
  status,
  thoughts,
  onViewFullPlan,
}: ArtifactSectionsProps) {
  const [collapsed, setCollapsed] = useState<CollapsibleState>({
    blueprint: false,
    storyboard: false,
    terminal: false,
  });

  return (
    <div className="flex flex-col gap-12">
      {/* Row A: Curriculum Plan */}
      <section className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        <div className="mb-6 flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <div className="bg-council-active/10 text-council-active ring-council-active/20 flex h-8 w-8 items-center justify-center rounded-lg ring-1">
              <Search className="h-4 w-4" />
            </div>
            <h3 className="text-foreground text-sm font-bold tracking-[0.15em] uppercase">
              Curriculum Plan
            </h3>
          </div>
          <button
            onClick={() => setCollapsed((prev) => ({ ...prev, blueprint: !prev.blueprint }))}
            className="text-micro text-text-muted hover:text-foreground font-bold tracking-widest uppercase transition-colors"
          >
            {collapsed.blueprint ? '[+] Expand' : '[-] Minimize'}
          </button>
        </div>

        <div
          className={cn(
            'transition-all duration-500',
            collapsed.blueprint ? 'h-0 overflow-hidden opacity-0' : 'opacity-100',
          )}
        >
          <CurriculumPlanView plan={plan} status={status} onViewFull={onViewFullPlan} />
        </div>
      </section>

      {/* Row B: Visual Storyboard */}
      <section className="animate-in fade-in slide-in-from-bottom-2 delay-75 duration-500">
        <div className="mb-6 flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <div className="bg-council-active/10 text-council-active ring-council-active/20 flex h-8 w-8 items-center justify-center rounded-lg ring-1">
              <Layout className="h-4 w-4" />
            </div>
            <h3 className="text-foreground text-sm font-bold tracking-[0.15em] uppercase">
              Visual Storyboard
            </h3>
          </div>
          <button
            onClick={() => setCollapsed((prev) => ({ ...prev, storyboard: !prev.storyboard }))}
            className="text-micro text-text-muted hover:text-foreground font-bold tracking-widest uppercase transition-colors"
          >
            {collapsed.storyboard ? '[+] Expand' : '[-] Minimize'}
          </button>
        </div>

        <div
          className={cn(
            'transition-all duration-500',
            collapsed.storyboard ? 'h-0 overflow-hidden opacity-0' : 'opacity-100',
          )}
        >
          <StoryboardView storyboard={storyboard} status={status} />
        </div>
      </section>

      {/* Row C: Council Stream (Terminal) */}
      <section className="animate-in fade-in slide-in-from-bottom-2 delay-150 duration-500">
        <div className="mb-6 flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <div className="bg-surface-border text-text-muted ring-surface-border flex h-8 w-8 items-center justify-center rounded-lg ring-1">
              <Terminal className="h-4 w-4" />
            </div>
            <div className="flex items-center gap-3">
              <h3 className="text-foreground text-sm font-bold tracking-[0.15em] uppercase">
                Council Stream
              </h3>
              <div className="bg-success/10 ring-success/20 flex items-center gap-1.5 rounded-full px-2 py-0.5 ring-1">
                <div className="bg-success shadow-glow-success h-1.5 w-1.5 animate-pulse rounded-full" />
                <span className="text-success font-mono text-[9px] font-bold uppercase">Live</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setCollapsed((prev) => ({ ...prev, terminal: !prev.terminal }))}
            className="text-micro text-text-muted hover:text-foreground font-bold tracking-widest uppercase transition-colors"
          >
            {collapsed.terminal ? '[+] Expand' : '[-] Minimize'}
          </button>
        </div>

        <div
          className={cn(
            'transition-all duration-500',
            collapsed.terminal ? 'h-0 overflow-hidden opacity-0' : 'opacity-100',
          )}
        >
          <CouncilDeliberation thoughts={thoughts} />
        </div>
      </section>
    </div>
  );
}
