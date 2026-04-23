import React from 'react';
import { JobStatus, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { HitlReviewPanel } from '@/components/orchestration/HitlReviewPanel';
import { LessonArtifactModal } from '@/components/orchestration/LessonModal';
import { PipelineHeader } from '@/components/orchestration/PipelineHeader';
import { RenderingMonitor } from '@/components/orchestration/RenderingMonitor';
import { ArtifactSections } from '@/components/orchestration/ArtifactSections';
import { FailedJobView } from '@/components/orchestration/FailedJobView';

interface GeneratingLessonViewProps {
  job: JobStatus;
  streamState: 'connecting' | 'connected' | 'error' | 'closed';
  streamError: Error | string | null;
}

/**
 * Top-level view for the active lesson generation pipeline.
 *
 * Composes the pipeline header, HITL review gate, rendering progress monitor,
 * artifact preview panels, and the full artifact modal into a single view
 * driven by the current job state.
 */
export function GeneratingLessonView({ job, streamState, streamError }: GeneratingLessonViewProps) {
  const [showDetails, setShowDetails] = React.useState(false);
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  const isFailed = job.status === 'failed' || streamState === 'error';

  if (isFailed) {
    const errorMsg = streamError instanceof Error ? streamError.message : String(streamError);
    return <FailedJobView errorMessage={job.error || errorMsg} />;
  }

  return (
    <div className="mx-auto max-w-7xl space-y-10 px-4 py-8 sm:px-6 lg:px-8">
      <PipelineHeader
        jobStatus={job.status}
        renderProgress={job.render_progress || 0}
        showDetails={showDetails}
        onHideDetails={() => setShowDetails(false)}
      />

      {job.status === 'awaiting_review' && job.plan && (
        <section className="animate-in fade-in slide-in-from-top-4 duration-700">
          <HitlReviewPanel
            jobId={job.job_id}
            plan={job.plan as CurriculumPlan}
            onActionComplete={() => {}}
          />
        </section>
      )}

      {job.status === 'rendering' && (
        <RenderingMonitor
          renderProgress={job.render_progress || 0}
          previewUrl={job.preview_url}
        />
      )}

      <ArtifactSections
        plan={(job.plan as CurriculumPlan) || null}
        storyboard={(job.storyboard as Storyboard) || null}
        status={job.status}
        thoughts={job.streamed_thoughts || []}
        onViewFullPlan={() => setIsModalOpen(true)}
      />

      <LessonArtifactModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        plan={(job.plan as CurriculumPlan) ?? null}
        storyboard={(job.storyboard as Storyboard) ?? null}
      />
    </div>
  );
}
