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
      size="xl"
    >
      {hasStoryboard ? (
        <div className="space-y-10 py-2">
          {storyboard!.scenes.map((scene) => (
            <div key={scene.scene_id} className="group relative space-y-4">
              <div className="flex items-center gap-4">
                <div className="bg-council-active/10 text-council-active ring-council-active/20 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-sm ring-1">
                  <span className="font-mono text-sm font-bold">{scene.scene_id}</span>
                </div>
                <div>
                  <h3 className="text-foreground text-lg leading-tight font-bold">{scene.title}</h3>
                  <p className="text-text-muted mt-0.5 text-[10px] font-bold tracking-[0.2em] uppercase opacity-60">
                    Sequence Identifier
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="border-surface-border bg-background/50 group-hover:border-council-active/20 relative overflow-hidden rounded-2xl border p-5 transition-colors">
                  <div className="absolute top-0 right-0 p-3 opacity-10">
                    <ArtifactBadge variant="active">VISUAL</ArtifactBadge>
                  </div>
                  <h4 className="text-council-active mb-3 text-[10px] font-bold tracking-widest uppercase">
                    Visual Composition
                  </h4>
                  <p className="text-text-muted text-sm leading-relaxed">{scene.description}</p>
                </div>
                <div className="border-council-active/10 bg-council-active/5 group-hover:bg-council-active/[0.08] relative overflow-hidden rounded-2xl border p-5 transition-colors">
                  <div className="absolute top-0 right-0 p-3 opacity-10">
                    <ArtifactBadge variant="completed">SCRIPT</ArtifactBadge>
                  </div>
                  <h4 className="text-council-active mb-3 text-[10px] font-bold tracking-widest uppercase">
                    Narration Script
                  </h4>
                  <p className="text-foreground text-sm leading-relaxed font-medium italic">
                    "{scene.narration}"
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : hasPlan ? (
        <div className="space-y-6">
          {plan!.teaching_steps.map((step) => (
            <div
              key={step.step_id}
              className="hover:bg-background/40 flex gap-6 rounded-xl p-4 transition-colors"
            >
              <div className="border-surface-border bg-background text-foreground flex h-10 w-10 shrink-0 items-center justify-center rounded-full border font-bold shadow-sm">
                {step.step_id}
              </div>
              <div className="space-y-2">
                <h3 className="text-foreground text-xl font-bold">{step.concept}</h3>
                <div className="flex flex-col gap-1">
                  <p className="text-text-muted text-sm leading-relaxed">
                    <span className="text-council-active mr-1 font-bold italic">Metaphor:</span>{' '}
                    {step.visual_metaphor}
                  </p>
                  <p className="border-surface-border bg-background/50 text-text-muted mt-2 rounded-xl border p-4 text-sm leading-relaxed whitespace-pre-wrap italic">
                    <ArtifactBadge variant="completed">NARRATION</ArtifactBadge>"{step.narration}"
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
