import React, { useMemo } from 'react';
import { JobStatus } from '@/lib/api/client';
import { useReducedMotion } from 'framer-motion';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { CouncilDeliberation } from '@/components/orchestration/Deliberation';
import { CollapsibleSection } from '@/components/orchestration/artifacts/CollapsibleSection';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';
import {
  Search,
  CheckCircle,
  Layout,
  Play,
  Activity,
  Users
} from 'lucide-react';


const PIPELINE_STEPS = [
  { id: 'planning', label: 'Pedagogy', agent: 'Analyst' },
  { id: 'validating', label: 'Audit', agent: 'Critic' },
  { id: 'architecting', label: 'Visuals', agent: 'Architect' },
  { id: 'animating', label: 'Motion', agent: 'Animator' },
  { id: 'rendering', label: 'Synthesis', agent: 'Manim' },
];

interface GeneratingLessonViewProps {
  /** The current state and artifacts of the generation job. */
  job: JobStatus;
  /** The status of the Server-Sent Events (SSE) connection. */
  streamState: 'connecting' | 'connected' | 'error' | 'closed';
  /** Any error encountered during thought streaming. */
  streamError: Error | null;
}

/**
 * A simple animated spinner component.
 *
 * @param {Object} props - Component properties.
 * @param {'sm' | 'md' | 'lg'} [props.size='md'] - The visual scale of the spinner.
 */
function LoadingSpinner({
  size = 'md',
  prefersReducedMotion = false,
}: {
  size?: 'sm' | 'md' | 'lg';
  prefersReducedMotion?: boolean;
}) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-10 h-10 border-3',
  };
  return (
    <div
      className={`${sizeClasses[size]} rounded-full border-[var(--surface-border)] border-t-indigo-500 ${prefersReducedMotion ? '' : 'animate-spin'}`}
    />
  );
}

/**
 * The primary view for observing an active lesson generation.
 *
 * This component visualizes the multi-agent orchestration by displaying
 * a live stream of agent thoughts, a pipeline progress indicator, and
 * real-time artifact previews (curriculum, storyboard, render progress).
 *
 * @param {GeneratingLessonViewProps} props - Component properties.
 * @returns {JSX.Element} The rendered generation view.
 */
export function GeneratingLessonView({ job, streamState, streamError }: GeneratingLessonViewProps) {
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [isPlanCollapsed, setIsPlanCollapsed] = React.useState(false);
  const [isStoryboardCollapsed, setIsStoryboardCollapsed] = React.useState(false);
  const [showDetails, setShowDetails] = React.useState(false);

  /**
   * Groups raw thought logs into displayable blocks by agent and phase.
   * Prevents flickering and provides a more readable "conversational" stream.
   */
  const thoughts = useMemo(() => {
    const rawThoughts = job?.streamed_thoughts ?? [];
    const groups: Array<{ agent: string; phase: string; content: string }> = [];

    for (const t of rawThoughts) {
      const agent = t.agent ?? 'system';
      const phase = t.phase ?? 'output';
      const content = (t.content ?? '').trim();
      if (!content) continue;

      const last = groups[groups.length - 1];
      if (last && last.agent === agent && last.phase === phase) {
        const separator =
          last.content.endsWith('.') || last.content.endsWith('!') || last.content.endsWith('?')
            ? ' '
            : ' ';
        last.content = (last.content + separator + content).replace(/\s+/g, ' ').trim();
      } else {
        groups.push({ agent, phase, content });
      }
    }
    return groups;
  }, [job?.streamed_thoughts]);

  if (streamError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center rounded-3xl border border-[var(--error-dim)] bg-[var(--surface)] p-8 text-center">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-8 w-8 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <h2 className="mb-4 text-2xl font-bold text-[var(--foreground)]">Connection Interrupted</h2>
        <p className="mb-8 max-w-sm leading-relaxed text-[var(--text-muted)]">
          The Council has disconnected or encountered a critical error while deliberating on your
          topic.
        </p>
        <div className="flex gap-4">
          <button
            onClick={() => window.location.reload()}
            className="rounded-xl bg-[var(--foreground)] px-8 py-3 text-xs font-bold tracking-widest text-[var(--background)] uppercase transition-opacity hover:opacity-90"
          >
            Try Reconnecting
          </button>
        </div>
      </div>
    );
  }

  if (!job || streamState === 'connecting') {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center space-y-6">
        <LoadingSpinner size="lg" prefersReducedMotion={prefersReducedMotion} />
        <div className={`text-center ${prefersReducedMotion ? '' : 'animate-pulse'}`}>
          <p className="mb-2 text-xs font-bold tracking-widest text-[var(--foreground)] uppercase">
            Summoning the Council
          </p>
          <p className="text-[10px] text-[var(--text-muted)] italic">
            Synchronizing pedagogical nodes...
          </p>
        </div>
      </div>
    );
  }

  // Completed State: Show Video Focus by default
  if (job.status === 'completed' && !showDetails) {
    return (
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-12 sm:px-6 lg:px-8">
        <div className="space-y-4 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--council-completed)]/20 bg-[var(--council-completed)]/10 px-4 py-1.5 text-[10px] font-bold tracking-widest text-[var(--council-completed)] uppercase">
            <CheckCircle className="h-3.5 w-3.5" />
            Generation Complete
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
            {job.topic}
          </h1>
          <p className="mx-auto max-w-2xl text-[13px] text-[var(--text-muted)] leading-relaxed">
            The council has successfully synthesized your requested concept. Explore the visual deliberation below or view the final result.
          </p>
        </div>

        <div className="aspect-video w-full overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--background)] shadow-2xl">
          <video
            src={job.video_url || ''}
            controls
            autoPlay
            className="h-full w-full object-contain"
          />
        </div>

        <div className="flex flex-col items-center gap-6 pt-4">
          <div className="flex gap-4">
            <button
              onClick={() => setShowDetails(true)}
              className="group flex items-center gap-3 rounded-xl border border-[var(--surface-border)] bg-[var(--surface)] px-6 py-3.5 text-[11px] font-bold tracking-widest text-[var(--foreground)] uppercase transition-all hover:border-[var(--council-active)]/50 hover:bg-[var(--background)]"
            >
              <Layout className="h-4 w-4 text-[var(--council-active)]" />
              Review Deliberation Details
            </button>
            <button
              onClick={() => window.location.href = '/jobs'}
              className="flex items-center gap-3 rounded-xl bg-[var(--foreground)] px-6 py-3.5 text-[11px] font-bold tracking-widest text-[var(--background)] uppercase transition-opacity hover:opacity-90"
            >
              Save to Library
            </button>
          </div>
        </div>
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
              <span className="text-sm font-bold tracking-widest text-[var(--foreground)] uppercase">
                Agent Council
              </span>
            </div>
            {job.status === 'completed' && showDetails && (
              <button
                onClick={() => setShowDetails(false)}
                className="flex items-center gap-2 rounded-lg border border-[var(--surface-border)] bg-[var(--surface)] px-3 py-1.5 text-[9px] font-bold tracking-widest text-[var(--foreground)] uppercase transition-colors hover:bg-[var(--background)]"
              >
                <Play className="h-3 w-3 text-[var(--council-active)]" />
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

              // Mock status messages based on job state
              const getStepStatus = () => {
                if (isPast) {
                  if (step.id === 'planning') return 'Content structure finalized.';
                  if (step.id === 'validating') return 'Validation successful.';
                  if (step.id === 'architecting') return 'Blueprints generated.';
                  if (step.id === 'animating') return 'Animation code ready.';
                  return 'Processing complete.';
                }
                if (isCurrent) {
                  if (step.id === 'animating') return `Processing scene ${job.render_progress || 1} physics`;
                  return 'Deliberating...';
                }
                return 'Waiting for output...';
              };

              return (
                <React.Fragment key={step.id}>
                  <div
                    className={`relative flex min-w-[200px] flex-1 items-center gap-3 rounded-xl border-2 p-3 transition-all duration-500 ${
                      isCurrent
                        ? 'border-[var(--council-active)] bg-[var(--council-active)]/5 shadow-[0_4px_12px_rgba(59,130,246,0.15)] ring-1 ring-[var(--council-active)]/30'
                        : isPast
                          ? 'border-[var(--council-completed)] bg-[var(--council-completed)]/5 opacity-100'
                          : 'border-[var(--surface-border)] bg-[var(--surface)] opacity-40'
                    }`}
                  >
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors duration-500 ${
                        isCurrent
                          ? 'bg-[var(--council-active)] text-white'
                          : isPast
                            ? 'bg-[var(--council-completed)]/20 text-[var(--council-completed)]'
                            : 'bg-[var(--surface-border)] text-[var(--text-muted)]'
                      }`}
                    >
                      {step.id === 'planning' && <Search className="h-4 w-4" />}
                      {step.id === 'validating' && <CheckCircle className="h-4 w-4" />}
                      {step.id === 'architecting' && <Layout className="h-4 w-4" />}
                      {step.id === 'animating' && <Play className="h-4 w-4" />}
                      {step.id === 'rendering' && <Activity className="h-4 w-4" />}
                    </div>

                    <div className="flex-1 overflow-hidden">
                      <div className="flex items-center justify-between mb-0.5">
                        <h4
                          className={`text-[11px] font-bold tracking-tight ${
                            isCurrent
                              ? 'text-[var(--foreground)]'
                              : isPast
                                ? 'text-[var(--council-completed)]'
                                : 'text-[var(--text-muted)]'
                          }`}
                        >
                          {step.agent}
                        </h4>
                        {isPast && (
                          <div className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[var(--council-completed)] text-white">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              className="h-2 w-2"
                              viewBox="0 0 20 20"
                              fill="currentColor"
                            >
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                        )}
                        {isCurrent && (
                          <div className="bg-[var(--council-active)] h-3.5 w-3.5 rounded-full flex items-center justify-center">
                            <span className="relative flex h-2 w-2">
                              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-100 opacity-75"></span>
                              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-white"></span>
                            </span>
                          </div>
                        )}
                      </div>
                      <p className="truncate text-[9px] font-medium text-[var(--text-muted)] opacity-70">
                        {getStepStatus()}
                      </p>
                    </div>
                  </div>

                  {idx < PIPELINE_STEPS.length - 1 && (
                    <div
                      className={`h-[2px] w-6 shrink-0 transition-colors duration-500 ${
                        isPast ? 'bg-[var(--council-completed)]' : 'bg-[var(--surface-border)]'
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
            {/* Reviewer placeholder if needed */}
            {(job.status === 'reviewing' || job.status === 'completed') && (
              <>
                <div className="h-[2px] w-6 shrink-0 bg-[var(--council-completed)]" />
                <div className="relative flex min-w-[240px] flex-1 items-center gap-4 rounded-xl border-2 border-[var(--council-completed)] bg-[var(--council-completed)]/5 p-4 opacity-100">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--council-completed)]/20 text-[var(--council-completed)]">
                    <Users className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-xs font-bold text-[var(--council-completed)]">Reviewer</h4>
                    <p className="text-[10px] text-[var(--text-muted)]">Awaiting final sign-off.</p>
                  </div>
                </div>
              </>
            )}
          </div>
        </section>

        {/* Curriculum Plan */}
        <section>
          <CollapsibleSection
            title="Curriculum Plan"
            isCollapsed={isPlanCollapsed}
            onToggle={() => setIsPlanCollapsed(!isPlanCollapsed)}
            badge={
              job.plan && (
                <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 font-mono text-[8px] text-indigo-500">
                  {job.plan.teaching_steps.length} STEPS
                </span>
              )
            }
          >
            <CurriculumPlanView 
              plan={job.plan ?? null} 
              status={job.status}
              onViewFull={() => setIsModalOpen(true)} 
            />
          </CollapsibleSection>
        </section>

        {/* Visual Storyboard */}
        <section>
          <CollapsibleSection
            title="Visual Storyboard"
            isCollapsed={isStoryboardCollapsed}
            onToggle={() => setIsStoryboardCollapsed(!isStoryboardCollapsed)}
            badge={
              job.status === 'rendering' && (
                <span className="animate-pulse font-mono text-[8px] text-indigo-400">
                  {Math.round(job.render_progress || 0)}% RENDERED
                </span>
              )
            }
          >
            <StoryboardView storyboard={job.storyboard ?? null} status={job.status} />
          </CollapsibleSection>
        </section>

        {/* System Log Terminal */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 px-2">
            <span className="text-sm font-bold tracking-widest text-[var(--foreground)] uppercase">
              System Log
            </span>
          </div>
          <CouncilDeliberation thoughts={thoughts} />
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
