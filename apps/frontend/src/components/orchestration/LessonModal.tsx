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
        <div className="space-y-8">
          {storyboard!.scenes.map((scene) => (
            <div key={scene.scene_id} className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="rounded bg-council-completed px-2 py-1 text-tiny font-bold text-white uppercase tracking-wider">
                  Scene {scene.scene_id}
                </span>
                <h3 className="text-lg font-bold text-foreground">{scene.title}</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-surface-border bg-background p-4">
                  <ArtifactBadge variant="active">Visual Composition</ArtifactBadge>
                  <p className="text-sm leading-relaxed text-text-muted">
                    {scene.description}
                  </p>
                </div>
                <div className="rounded-xl border border-council-active/10 bg-council-active/5 p-4">
                  <ArtifactBadge variant="completed">Narration Script</ArtifactBadge>
                  <p className="text-sm text-foreground italic leading-relaxed">"{scene.narration}"</p>
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
