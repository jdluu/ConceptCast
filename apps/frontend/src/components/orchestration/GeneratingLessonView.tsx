import React, { useMemo, useState } from 'react';
import { cn } from '@/lib/utils';
import { JobStatus } from '@/lib/api/client';
import { motion, useReducedMotion } from 'framer-motion';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { CollapsibleSection } from '@/components/orchestration/artifacts/CollapsibleSection';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { AnalystVerdict } from '@/components/orchestration/AnalystVerdict';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';
import {
  Search,
  CheckCircle,
  Layout,
  Play,
  Activity,
  ArrowRight,
  Sparkles,
  Info,
  Terminal,
} from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'planning', agent: 'Pedagogue' },
  { id: 'validating', agent: 'Validator' },
  { id: 'architecting', agent: 'Architect' },
  { id: 'animating', agent: 'Animator' },
  { id: 'rendering', agent: 'Manim' },
];

interface LoadingIndicatorProps {
  size?: 'sm' | 'md' | 'lg';
}

function LoadingIndicator({ size = 'md' }: LoadingIndicatorProps) {
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;

  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-10 w-10 border-2',
    lg: 'h-16 w-16 border-4',
  };

  return (
    <div
      className={`${sizeClasses[size]} rounded-full border-surface-border border-t-council-active ${prefersReducedMotion ? '' : 'animate-spin'}`}
    />
  );
}

/**
 * Renders a single stage of the agent council pipeline.
 * Centralizes complex Tailwind utility chains for better maintainability.
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
        'relative flex min-w-xs flex-1 items-center gap-3 rounded-xl border-2 p-3 transition-all duration-500',
        isCurrent
          ? 'border-council-active bg-council-active/5 shadow-glow-council ring-1 ring-council-active/30'
          : isPast
            ? 'border-council-completed bg-council-completed/5 opacity-100'
            : 'border-surface-border bg-surface opacity-40',
      )}
    >
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-500',
          isCurrent
            ? 'bg-council-active text-white'
            : isPast
              ? 'bg-council-completed/20 text-council-completed'
              : 'bg-surface-border text-text-muted',
        )}
      >
        <Icon className="h-4 w-4" />
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="flex items-center justify-between mb-0.5">
          <h4
            className={cn(
              'text-mini font-bold tracking-tight',
              isCurrent
                ? 'text-foreground'
                : isPast
                  ? 'text-council-completed'
                  : 'text-text-muted',
            )}
          >
            {step.agent}
          </h4>
          {isPast && (
            <div className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-council-completed text-white">
              <CheckCircle className="h-2 w-2" />
            </div>
          )}
          {isCurrent && (
            <div className="bg-council-active h-3.5 w-3.5 rounded-full flex items-center justify-center">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-info/20 opacity-75"></span>
                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white"></span>
              </span>
            </div>
          )}
        </div>
        <p className="truncate text-micro font-medium text-text-muted opacity-70">
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

/**
 * The primary view for observing an active lesson generation.
 */
export function GeneratingLessonView({ job, streamState, streamError }: GeneratingLessonViewProps) {
  const [showDetails, setShowDetails] = React.useState(false);
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  
  // Collapse state
  const [collapsed, setCollapsed] = useState({
    blueprint: false,
    storyboard: false,
    validation: true
  });

  const isFailed = job.status === 'failed' || streamState === 'error';

  const currentStep = useMemo(() => {
    return PIPELINE_STEPS.find((s) => s.id === job.status) || PIPELINE_STEPS[0];
  }, [job.status]);

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
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6 lg:px-8">
      {/* Header & Pipeline Progress */}
      <div className="space-y-8">
        {/* Agent Council Pipeline */}
        <section className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold tracking-widest text-foreground uppercase">
                Agent Council
              </span>
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
          <div className="flex w-full items-center gap-4 overflow-x-auto pb-4">
            {PIPELINE_STEPS.map((step, idx) => {
              const isCurrent = job.status === step.id;
              const isPast =
                PIPELINE_STEPS.findIndex((s) => s.id === job.status) > idx ||
                job.status === 'completed';

              const statusMessage = (() => {
                if (isPast) {
                  if (step.id === 'planning') return 'Content structure finalized.';
                  if (step.id === 'validating') return 'Validation successful.';
                  if (step.id === 'architecting') return 'Blueprints generated.';
                  if (step.id === 'animating') return 'Animation code ready.';
                  return 'Processing complete.';
                }
                if (isCurrent) {
                  if (step.id === 'animating')
                    return `Processing scene ${job.render_progress || 1} physics`;
                  return 'Deliberating...';
                }
                return 'Waiting for output...';
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
                        'h-0.5 w-6 shrink-0 transition-colors duration-500',
                        isPast ? 'bg-council-completed' : 'bg-surface-border',
                      )}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </section>

        {/* Hero Transition: From Deliberation to Rendering */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Main Monitor */}
          <div className="lg:col-span-2">
            <div className="relative overflow-hidden rounded-3xl border border-surface-border bg-surface shadow-2xl transition-all duration-700">
              <div className="flex items-center justify-between border-b border-surface-border/50 bg-surface/50 px-6 py-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-council-active/10 text-council-active shadow-sm">
                    {job.status === 'rendering' ? (
                      <Activity className="h-4 w-4" />
                    ) : (
                      <Sparkles className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <h2 className="text-sm font-bold tracking-tight text-foreground">
                      {job.status === 'rendering' ? 'Synthesis Monitor' : 'Council Chambers'}
                    </h2>
                    <p className="text-tiny font-medium text-text-muted uppercase tracking-widest opacity-60">
                      Phase: {job.status}
                    </p>
                  </div>
                </div>
                {job.status === 'rendering' && (
                  <div className="flex items-center gap-4">
                    <div className="hidden text-right sm:block">
                      <div className="text-tiny font-bold text-text-muted uppercase tracking-tighter">
                        Render Progress
                      </div>
                      <div className="text-sm font-mono font-bold text-council-active">
                        {Math.round(job.render_progress || 0)}%
                      </div>
                    </div>
                    <LoadingIndicator size="sm" />
                  </div>
                )}
              </div>

              <div className="aspect-video bg-background p-8">
                {job.status === 'rendering' ? (
                  <div className="flex h-full flex-col items-center justify-center space-y-8">
                    <div className="relative h-48 w-48">
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
                        <motion.circle
                          cx="50"
                          cy="50"
                          r="45"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray="283"
                          animate={{
                            strokeDashoffset: 283 - (283 * (job.render_progress || 0)) / 100,
                          }}
                          className="text-council-active"
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-4xl font-mono font-bold text-foreground">
                          {Math.round(job.render_progress || 0)}%
                        </span>
                        <span className="text-tiny font-bold text-text-muted uppercase tracking-widest">
                          Frames Ready
                        </span>
                      </div>
                    </div>
                    <div className="text-center">
                      <h3 className="mb-2 text-xl font-bold text-foreground">
                        Materializing Mathematics
                      </h3>
                      <p className="max-w-xs text-sm text-text-muted">
                        The Animator is executing Manim code to generate high-fidelity educational
                        assets.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="mb-8 relative">
                      <div className="absolute -inset-4 rounded-full bg-council-active/10 blur-2xl animate-pulse" />
                      <LoadingIndicator size="lg" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="text-2xl font-bold tracking-tight text-foreground">
                        Agent {currentStep?.agent} is deliberating
                      </h3>
                      <div className="flex items-center justify-center gap-2">
                        <span className="h-1 w-1 rounded-full bg-council-active animate-bounce" />
                        <span
                          className="h-1 w-1 rounded-full bg-council-active animate-bounce"
                          style={{ animationDelay: '0.2s' }}
                        />
                        <span
                          className="h-1 w-1 rounded-full bg-council-active animate-bounce"
                          style={{ animationDelay: '0.4s' }}
                        />
                        <p className="text-sm font-medium text-text-muted italic ml-1">
                          Analyzing {job.topic}...
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Thought Feed Mini-Overlay */}
              <div className="absolute bottom-6 left-6 right-6">
                <div className="flex items-center gap-3 rounded-2xl border border-surface-border bg-surface/80 p-4 backdrop-blur-md shadow-lg">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-background text-council-active border border-surface-border">
                    <Terminal className="h-4 w-4" />
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-council-active/10 px-2 py-0.5 font-mono text-nano text-council-active">
                        LATEST_THOUGHT
                      </span>
                      <span className="text-tiny font-bold text-text-muted uppercase tracking-widest">
                        {job.streamed_thoughts?.[job.streamed_thoughts.length - 1]?.agent ||
                          'System'}
                      </span>
                    </div>
                    <p className="truncate font-mono text-mini text-foreground opacity-80">
                      {job.streamed_thoughts?.[job.streamed_thoughts.length - 1]?.content ||
                        'Initializing council synchronization protocol...'}
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-text-muted opacity-40" />
                </div>
              </div>
            </div>
          </div>

          {/* Side Feed: Global Thought Stream */}
          <div className="space-y-6">
            <div className="flex h-full flex-col">
              <div className="mb-4 flex items-center justify-between px-2">
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-text-muted" />
                  <span className="text-tiny font-bold tracking-[0.2em] text-text-muted uppercase">
                    Council Stream
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-success shadow-glow-success" />
                  <span className="animate-pulse font-mono text-nano text-council-active">
                    LIVE
                  </span>
                </div>
              </div>
              <div className="flex-1">
                <CouncilDeliberation thoughts={job.streamed_thoughts || []} />
              </div>
            </div>
          </div>
        </div>

        {/* Artifact Preview Area */}
        <section className="mt-8 space-y-6">
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-text-muted" />
              <span className="text-tiny font-bold tracking-[0.2em] text-text-muted uppercase">
                Artifact Previews
              </span>
            </div>
            {(job.plan || job.storyboard) && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="text-tiny font-bold text-council-active uppercase tracking-widest hover:underline"
              >
                Expand View
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <CollapsibleSection 
              title="Pedagogical Blueprint" 
              isCollapsed={collapsed.blueprint}
              onToggle={() => setCollapsed(prev => ({ ...prev, blueprint: !prev.blueprint }))}
            >
              <CurriculumPlanView
                plan={job.plan as any}
                status={job.status}
                onViewFull={() => setIsModalOpen(true)}
              />
            </CollapsibleSection>

            <CollapsibleSection 
              title="Visual Storyboard" 
              isCollapsed={collapsed.storyboard}
              onToggle={() => setCollapsed(prev => ({ ...prev, storyboard: !prev.storyboard }))}
            >
              <StoryboardView
                storyboard={job.storyboard as any}
                status={job.status}
              />
            </CollapsibleSection>

            {job.validation && (
              <div className="md:col-span-2">
                <CollapsibleSection 
                  title="Council Validation Feedback" 
                  isCollapsed={collapsed.validation}
                  onToggle={() => setCollapsed(prev => ({ ...prev, validation: !prev.validation }))}
                >
                  <AnalystVerdict validation={job.validation} />
                </CollapsibleSection>
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Full Artifact Modal */}
      <LessonArtifactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        plan={job.plan ?? null}
        storyboard={job.storyboard ?? null}
      />
    </div>
  );
}
