import { Modal } from '@/components/ui/Common';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { ArtifactBadge } from './artifacts/ArtifactCommon';

interface LessonModalProps {
  isOpen: boolean;
  onClose: () => void;
  plan: CurriculumPlan | null;
  storyboard: Storyboard | null;
}

export function LessonArtifactModal({ isOpen, onClose, plan, storyboard }: LessonModalProps) {
  const hasStoryboard = !!storyboard;
  const hasPlan = !!plan;

  if (!hasStoryboard && !hasPlan) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={hasStoryboard ? 'Full Visual Storyboard' : 'Complete Curriculum Plan'}
    >
      {hasStoryboard ? (
        <div className="space-y-10 py-2">
          {storyboard!.scenes.map((scene) => (
            <div key={scene.scene_id} className="group relative space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-council-active/10 text-council-active shadow-sm ring-1 ring-council-active/20">
                  <span className="font-mono text-sm font-bold">{scene.scene_id}</span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground leading-tight">{scene.title}</h3>
                  <p className="text-[10px] font-bold tracking-[0.2em] text-text-muted uppercase opacity-60 mt-0.5">
                    Sequence Identifier
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="relative overflow-hidden rounded-2xl border border-surface-border bg-background/50 p-5 transition-colors group-hover:border-council-active/20">
                  <div className="absolute top-0 right-0 p-3 opacity-10">
                    <ArtifactBadge variant="active">VISUAL</ArtifactBadge>
                  </div>
                  <h4 className="mb-3 text-[10px] font-bold tracking-widest text-council-active uppercase">
                    Visual Composition
                  </h4>
                  <p className="text-sm leading-relaxed text-text-muted">
                    {scene.description}
                  </p>
                </div>
                <div className="relative overflow-hidden rounded-2xl border border-council-active/10 bg-council-active/5 p-5 transition-colors group-hover:bg-council-active/[0.08]">
                  <div className="absolute top-0 right-0 p-3 opacity-10">
                    <ArtifactBadge variant="completed">SCRIPT</ArtifactBadge>
                  </div>
                  <h4 className="mb-3 text-[10px] font-bold tracking-widest text-council-active uppercase">
                    Narration Script
                  </h4>
                  <p className="text-sm text-foreground italic leading-relaxed font-medium">
                    "{scene.narration}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : hasPlan ? (
        <div className="space-y-6">
          <div className="mb-8 rounded-xl border border-council-active/20 bg-council-active/10 p-4">
            <ArtifactBadge variant="active">Target Audience</ArtifactBadge>
            <p className="text-lg font-bold text-foreground">{plan!.target_audience}</p>
          </div>
          {plan!.teaching_steps.map((step) => (
            <div
              key={step.step_id}
              className="flex gap-6 rounded-xl p-4 transition-colors hover:bg-background/40"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-surface-border bg-background font-bold text-foreground shadow-sm">
                {step.step_id}
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-foreground">{step.concept}</h3>
                <div className="flex flex-col gap-1">
                  <p className="text-sm leading-relaxed text-text-muted">
                    <span className="font-bold text-council-active italic mr-1">Metaphor:</span>{' '}
                    {step.visual_metaphor}
                  </p>
                  <p className="mt-2 rounded-xl border border-surface-border bg-background/50 p-4 text-sm whitespace-pre-wrap text-text-muted italic leading-relaxed">
                    <ArtifactBadge variant="completed">NARRATION</ArtifactBadge>
                    "{step.narration}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </Modal>
  );
}
