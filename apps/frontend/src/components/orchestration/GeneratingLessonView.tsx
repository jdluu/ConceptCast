import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { JobStatus, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { motion } from 'framer-motion';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { AnalystVerdict } from '@/components/orchestration/AnalystVerdict';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';
import { HitlReviewPanel } from '@/components/orchestration/HitlReviewPanel';
import {
  Search,
  CheckCircle,
  Layout,
  Play,
  Activity,
  Sparkles,
  Terminal,
  ShieldCheck,
} from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'planning', agent: 'Pedagogue', label: 'Plan' },
  { id: 'validating', agent: 'Validator', label: 'Audit' },
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
      validating: CheckCircle,
      architecting: Layout,
      animating: Play,
      rendering: Activity,
    }[step.id] || Activity;

  return (
    <div
      className={cn(
        'relative flex min-w-[160px] flex-1 items-center gap-2.5 rounded-xl border p-2.5 transition-all duration-500 sm:min-w-[200px]',
        isCurrent
          ? 'border-council-active bg-council-active/5 shadow-glow-council ring-1 ring-council-active/20'
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
            isCurrent
              ? 'text-foreground'
              : isPast
                ? 'text-success'
                : 'text-text-muted',
          )}
        >
          {step.agent}
        </h4>
        <p className="truncate text-[9px] font-medium text-text-muted opacity-70">
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
    terminal: false
  });

  const isFailed = job.status === 'failed' || streamState === 'error';

  if (isFailed) {
    const errorMsg = streamError instanceof Error ? streamError.message : String(streamError);
    return (
      <div className="flex min-h-md flex-col items-center justify-center p-8 text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-destructive/20 bg-destructive/10 text-destructive">
          <Activity className="h-8 w-8" />
        </div>
        <h2 className="mb-2 text-2xl font-bold text-foreground">Orchestration Halted</h2>
        <p className="mb-8 max-w-md text-text-muted">
          {job.error || errorMsg || 'The council encountered an unexpected synchronization error.'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="rounded-xl bg-foreground px-8 py-3 font-bold text-background transition-opacity hover:opacity-90"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-10 px-4 py-8 sm:px-6 lg:px-8">
      {/* 1. Agent Council Pipeline (Header) */}
      <section className="space-y-6">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-council-active/10 text-council-active shadow-glow-council ring-1 ring-council-active/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">Agent Council</h1>
              <p className="text-tiny font-bold tracking-[0.2em] text-text-muted uppercase opacity-60">
                Orchestration Pipeline
              </p>
            </div>
          </div>
          {job.status === 'completed' && showDetails && (
            <button
              onClick={() => setShowDetails(false)}
              className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-1.5 text-micro font-bold tracking-widest text-foreground uppercase transition-colors hover:bg-background"
            >
              <Play className="h-3 w-3 text-council-active" />
              Back to Video
            </button>
          )}
        </div>

        <div className="flex w-full items-center gap-2 overflow-x-auto pb-4 custom-scrollbar sm:gap-3">
          {PIPELINE_STEPS.map((step, idx) => {
            const isCurrent = job.status === step.id || (step.id === 'planning' && job.status === 'awaiting_review');
            const isPast =
              (PIPELINE_STEPS.findIndex((s) => s.id === job.status) > idx && job.status !== 'awaiting_review') ||
              job.status === 'completed';

            const statusMessage = (() => {
              if (isPast) {
                if (step.id === 'planning') return 'Structure finalized';
                if (step.id === 'validating') return 'Quality verified';
                if (step.id === 'architecting') return 'Scenes mapped';
                if (step.id === 'animating') return 'Script ready';
                return 'Complete';
              }
              if (isCurrent) {
                if (step.id === 'animating') return `Scene ${job.render_progress || 1} logic`;
                if (step.id === 'rendering') return `${Math.round(job.render_progress || 0)}% frames`;
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
                      'h-0.5 w-3 shrink-0 sm:w-6 transition-colors duration-500',
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
          <div className="relative overflow-hidden rounded-3xl border border-council-active/20 bg-surface p-12 shadow-2xl backdrop-blur-sm">
            <div className="mx-auto flex max-w-md flex-col items-center text-center">
              <div className="relative mb-10 h-48 w-48">
                <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="2" className="text-surface-border" />
                  <motion.circle
                    cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="3" strokeDasharray="283"
                    animate={{ strokeDashoffset: 283 - (283 * (job.render_progress || 0)) / 100 }}
                    className="text-council-active"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-5xl font-mono font-bold text-foreground tracking-tighter">
                    {Math.round(job.render_progress || 0)}%
                  </span>
                  <span className="text-micro font-bold text-text-muted uppercase tracking-[0.2em]">Frames Synced</span>
                </div>
              </div>
              <h2 className="mb-3 text-2xl font-bold text-foreground tracking-tight">Materializing Mathematics</h2>
              <p className="text-sm text-text-muted leading-relaxed">
                The Animator is executing Manim code to generate high-fidelity educational assets at 60 frames per second.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* 4. Artifact Previews (Primary View) - Stacked Rows */}
      <div className="flex flex-col gap-12">
        {/* Row A: Pedagogical Blueprint */}
        <section className="animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="mb-6 flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-council-active/10 text-council-active ring-1 ring-council-active/20">
                <Search className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold tracking-[0.15em] text-foreground uppercase">
                Pedagogical Blueprint
              </h3>
            </div>
            <button 
              onClick={() => setCollapsed(prev => ({ ...prev, blueprint: !prev.blueprint }))}
              className="text-micro font-bold text-text-muted uppercase tracking-widest hover:text-foreground transition-colors"
            >
              {collapsed.blueprint ? '[+] Expand' : '[-] Minimize'}
            </button>
          </div>
          
          <div className={cn("transition-all duration-500", collapsed.blueprint ? "h-0 opacity-0 overflow-hidden" : "opacity-100")}>
            <CurriculumPlanView
              plan={job.plan as CurriculumPlan || null}
              status={job.status}
              onViewFull={() => setIsModalOpen(true)}
            />
            
            {/* Embedded Verdict when available */}
            {job.validation && (
              <div className="mt-8 animate-in fade-in slide-in-from-top-2 duration-500">
                <div className="mb-4 flex items-center gap-3 px-2">
                  <ShieldCheck className="h-4 w-4 text-success" />
                  <span className="text-tiny font-bold tracking-widest text-success uppercase">Pedagogical Audit Verdict</span>
                </div>
                <AnalystVerdict validation={job.validation} />
              </div>
            )}
          </div>
        </section>

        {/* Row B: Visual Storyboard */}
        <section className="animate-in fade-in slide-in-from-bottom-2 delay-75 duration-500">
          <div className="mb-6 flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-council-active/10 text-council-active ring-1 ring-council-active/20">
                <Layout className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-bold tracking-[0.15em] text-foreground uppercase">
                Visual Storyboard
              </h3>
            </div>
            <button 
              onClick={() => setCollapsed(prev => ({ ...prev, storyboard: !prev.storyboard }))}
              className="text-micro font-bold text-text-muted uppercase tracking-widest hover:text-foreground transition-colors"
            >
              {collapsed.storyboard ? '[+] Expand' : '[-] Minimize'}
            </button>
          </div>
          
          <div className={cn("transition-all duration-500", collapsed.storyboard ? "h-0 opacity-0 overflow-hidden" : "opacity-100")}>
            <StoryboardView
              storyboard={job.storyboard as Storyboard || null}
              status={job.status}
            />
          </div>
        </section>

        {/* Row C: Council Stream (Terminal) */}
        <section className="animate-in fade-in slide-in-from-bottom-2 delay-150 duration-500">
          <div className="mb-6 flex items-center justify-between px-2">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-border text-text-muted ring-1 ring-surface-border">
                <Terminal className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-bold tracking-[0.15em] text-foreground uppercase">
                  Council Intelligence Stream
                </h3>
                <div className="flex items-center gap-1.5 rounded-full bg-success/10 px-2 py-0.5 ring-1 ring-success/20">
                  <div className="h-1.5 w-1.5 rounded-full bg-success animate-pulse shadow-glow-success" />
                  <span className="font-mono text-[9px] font-bold text-success uppercase">Live</span>
                </div>
              </div>
            </div>
            <button 
              onClick={() => setCollapsed(prev => ({ ...prev, terminal: !prev.terminal }))}
              className="text-micro font-bold text-text-muted uppercase tracking-widest hover:text-foreground transition-colors"
            >
              {collapsed.terminal ? '[+] Expand' : '[-] Minimize'}
            </button>
          </div>
          
          <div className={cn("transition-all duration-500", collapsed.terminal ? "h-0 opacity-0 overflow-hidden" : "opacity-100")}>
            <CouncilDeliberation thoughts={job.streamed_thoughts || []} />
          </div>
        </section>
      </div>

      {/* Full Artifact Modal */}
      <LessonArtifactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        plan={job.plan as CurriculumPlan ?? null}
        storyboard={job.storyboard as Storyboard ?? null}
      />
    </div>
  );
}
