import React from 'react';
import { cn } from '@/lib/utils';
import { Search, CheckCircle, Layout, Play, Activity, Sparkles } from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'planning', agent: 'Planner', label: 'Plan' },
  { id: 'architecting', agent: 'Architect', label: 'Design' },
  { id: 'animating', agent: 'Animator', label: 'Script' },
  { id: 'rendering', agent: 'Manim', label: 'Render' },
] as const;

type PipelineStep = (typeof PIPELINE_STEPS)[number];

/**
 * Renders a single stage of the agent council pipeline.
 */
function PipelineStepCard({
  step,
  isCurrent,
  isPast,
  statusMessage,
}: {
  step: PipelineStep;
  isCurrent: boolean;
  isPast: boolean;
  statusMessage: string;
}) {
  const Icon =
    {
      planning: Search,
      architecting: Layout,
      animating: Play,
      rendering: Activity,
    }[step.id] || Activity;

  return (
    <div
      className={cn(
        'relative flex min-w-[160px] flex-1 items-center gap-2.5 rounded-xl border p-2.5 transition-all duration-500 sm:min-w-[200px]',
        isCurrent
          ? 'border-council-active bg-council-active/5 shadow-glow-council ring-council-active/20 ring-1'
          : isPast
            ? 'border-success/30 bg-success/5 opacity-100'
            : 'border-surface-border bg-surface opacity-40',
      )}
    >
      <div
        className={cn(
          'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-500',
          isCurrent
            ? 'bg-council-active text-white'
            : isPast
              ? 'bg-success text-white'
              : 'bg-surface-border text-text-muted',
        )}
      >
        {isPast ? <CheckCircle className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
      </div>

      <div className="flex-1 overflow-hidden">
        <h4
          className={cn(
            'text-[10px] font-bold tracking-wider uppercase',
            isCurrent ? 'text-foreground' : isPast ? 'text-success' : 'text-text-muted',
          )}
        >
          {step.agent}
        </h4>
        <p className="text-text-muted truncate text-[9px] font-medium opacity-70">
          {statusMessage}
        </p>
      </div>
    </div>
  );
}

interface PipelineHeaderProps {
  jobStatus: string;
  renderProgress: number;
  showDetails: boolean;
  onHideDetails: () => void;
}

/**
 * Renders the pipeline header: title bar and horizontal step card strip.
 */
export function PipelineHeader({
  jobStatus,
  renderProgress,
  showDetails,
  onHideDetails,
}: PipelineHeaderProps) {
  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between px-2">
        <div className="flex items-center gap-3">
          <div className="bg-council-active/10 text-council-active shadow-glow-council ring-council-active/20 flex h-10 w-10 items-center justify-center rounded-xl ring-1">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-foreground text-xl font-bold tracking-tight">Agent Council</h1>
            <p className="text-tiny text-text-muted font-bold tracking-[0.2em] uppercase opacity-60">
              Generation Pipeline
            </p>
          </div>
        </div>
        {jobStatus === 'completed' && showDetails && (
          <button
            onClick={onHideDetails}
            className="border-surface-border bg-surface text-micro text-foreground hover:bg-background flex items-center gap-2 rounded-lg border px-3 py-1.5 font-bold tracking-widest uppercase transition-colors"
          >
            <Play className="text-council-active h-3 w-3" />
            Back to Video
          </button>
        )}
      </div>

      <div className="custom-scrollbar flex w-full items-center gap-2 overflow-x-auto pb-4 sm:gap-3">
        {PIPELINE_STEPS.map((step, idx) => {
          const isCurrent =
            jobStatus === step.id || (step.id === 'planning' && jobStatus === 'awaiting_review');
          const isPast =
            (PIPELINE_STEPS.findIndex((s) => s.id === jobStatus) > idx &&
              jobStatus !== 'awaiting_review') ||
            jobStatus === 'completed';

          const statusMessage = (() => {
            if (isPast) {
              if (step.id === 'planning') return 'Structure finalized';
              if (step.id === 'architecting') return 'Scenes mapped';
              if (step.id === 'animating') return 'Script ready';
              return 'Complete';
            }
            if (isCurrent) {
              if (step.id === 'animating') return `Scene ${renderProgress || 1} logic`;
              if (step.id === 'rendering')
                return `${Math.round(renderProgress || 0)}% frames`;
              return 'Working...';
            }
            return 'Queued';
          })();

          return (
            <React.Fragment key={step.id}>
              <PipelineStepCard
                step={step}
                isCurrent={isCurrent}
                isPast={isPast}
                statusMessage={statusMessage}
              />

              {idx < PIPELINE_STEPS.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 w-3 shrink-0 transition-colors duration-500 sm:w-6',
                    isPast ? 'bg-success/30' : 'bg-surface-border',
                  )}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </section>
  );
}
