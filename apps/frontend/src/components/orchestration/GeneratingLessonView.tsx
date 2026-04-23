import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { JobStatus, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { LazyMotion, domAnimation } from 'motion/react';
import * as m from 'motion/react-m';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';
import { HitlReviewPanel } from '@/components/orchestration/HitlReviewPanel';
import { Search, CheckCircle, Layout, Play, Activity, Sparkles, Terminal } from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'planning', agent: 'Planner', label: 'Plan' },
  { id: 'architecting', agent: 'Architect', label: 'Design' },
  { id: 'animating', agent: 'Animator', label: 'Script' },
  { id: 'rendering', agent: 'Manim', label: 'Render' },
];

/**
 * Renders a single stage of the agent council pipeline.
 */
function PipelineStepCard({
  step,
  isCurrent,
  isPast,
  statusMessage,
}: {
  step: (typeof PIPELINE_STEPS)[0];
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

interface GeneratingLessonViewProps {
  job: JobStatus;
  streamState: 'connecting' | 'connected' | 'error' | 'closed';
  streamError: Error | string | null;
}

export function GeneratingLessonView({ job, streamState, streamError }: GeneratingLessonViewProps) {
  const [showDetails, setShowDetails] = React.useState(false);
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  const [collapsed, setCollapsed] = useState({
    blueprint: false,
    storyboard: false,
    terminal: false,
  });

  const isFailed = job.status === 'failed' || streamState === 'error';

  if (isFailed) {
    const errorMsg = streamError instanceof Error ? streamError.message : String(streamError);
    return (
      <div className="min-h-md flex flex-col items-center justify-center p-8 text-center">
        <div className="border-destructive/20 bg-destructive/10 text-destructive mb-6 flex h-16 w-16 items-center justify-center rounded-full border">
          <Activity className="h-8 w-8" />
        </div>
        <h2 className="text-foreground mb-2 text-2xl font-bold">Generation Halted</h2>
        <p className="text-text-muted mb-8 max-w-md">
          {job.error || errorMsg || 'The council encountered an unexpected synchronization error.'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-foreground text-background rounded-xl px-8 py-3 font-bold transition-opacity hover:opacity-90"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-10 px-4 py-8 sm:px-6 lg:px-8">
      {/* 1. Generation Pipeline (Header) */}
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
          {job.status === 'completed' && showDetails && (
            <button
              onClick={() => setShowDetails(false)}
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
              job.status === step.id ||
              (step.id === 'planning' && job.status === 'awaiting_review');
            const isPast =
              (PIPELINE_STEPS.findIndex((s) => s.id === job.status) > idx &&
                job.status !== 'awaiting_review') ||
              job.status === 'completed';

            const statusMessage = (() => {
              if (isPast) {
                if (step.id === 'planning') return 'Structure finalized';
                if (step.id === 'architecting') return 'Scenes mapped';
                if (step.id === 'animating') return 'Script ready';
                return 'Complete';
              }
              if (isCurrent) {
                if (step.id === 'animating') return `Scene ${job.render_progress || 1} logic`;
                if (step.id === 'rendering')
                  return `${Math.round(job.render_progress || 0)}% frames`;
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

      {/* 2. Human in the Loop (Priority Alert) */}
      {job.status === 'awaiting_review' && job.plan && (
        <section className="animate-in fade-in slide-in-from-top-4 duration-700">
          <HitlReviewPanel
            jobId={job.job_id}
            plan={job.plan as CurriculumPlan}
            onActionComplete={() => {}}
          />
        </section>
      )}

      {/* 3. Rendering Monitor (Visible only during render) */}
      {job.status === 'rendering' && (
        <section className="animate-in fade-in zoom-in-95 duration-700">
          <div className="border-council-active/20 bg-surface relative overflow-hidden rounded-3xl border p-12 shadow-2xl backdrop-blur-sm">
            {job.preview_url && (
              <div className="absolute inset-0 opacity-10">
                <img
                  src={job.preview_url}
                  alt="Preview"
                  className="h-full w-full object-cover blur-sm"
                />
              </div>
            )}
            <div className="relative z-10 mx-auto flex max-w-md flex-col items-center text-center">
              <div className="relative mb-10 h-48 w-48">
                {job.preview_url && (
                  <div className="absolute inset-4 overflow-hidden rounded-full opacity-40">
                    <img
                      src={job.preview_url}
                      alt="Preview"
                      className="h-full w-full object-cover"
                    />
                  </div>
                )}
                <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="text-surface-border"
                  />
                  <LazyMotion features={domAnimation}>
                    <m.circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeDasharray="283"
                      animate={{ strokeDashoffset: 283 - (283 * (job.render_progress || 0)) / 100 }}
                      className="text-council-active"
                    />
                  </LazyMotion>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-foreground font-mono text-5xl font-bold tracking-tighter">
                    {Math.round(job.render_progress || 0)}%
                  </span>
                  <span className="text-micro text-text-muted font-bold tracking-[0.2em] uppercase">
                    Frames rendered
                  </span>
                </div>
              </div>
              <h2 className="text-foreground mb-3 text-2xl font-bold tracking-tight">
                Rendering video
              </h2>
              <p className="text-text-muted text-sm leading-relaxed">
                The Animator is executing Manim code to generate high-fidelity educational assets at
                60 frames per second.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* 4. Artifact Previews (Primary View) - Stacked Rows */}
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
            <CurriculumPlanView
              plan={(job.plan as CurriculumPlan) || null}
              status={job.status}
              onViewFull={() => setIsModalOpen(true)}
            />
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
            <StoryboardView
              storyboard={(job.storyboard as Storyboard) || null}
              status={job.status}
            />
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
                  <span className="text-success font-mono text-[9px] font-bold uppercase">
                    Live
                  </span>
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
            <CouncilDeliberation thoughts={job.streamed_thoughts || []} />
          </div>
        </section>
      </div>

      {/* Full Artifact Modal */}
      <LessonArtifactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        plan={(job.plan as CurriculumPlan) ?? null}
        storyboard={(job.storyboard as Storyboard) ?? null}
      />
    </div>
  );
}
