import { Modal } from '@/components/ui/Common';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';

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
                <span className="rounded bg-indigo-500 px-2 py-1 text-[10px] font-bold text-white">
                  SCENE {scene.scene_id}
                </span>
                <h3 className="text-lg font-bold text-[var(--foreground)]">{scene.title}</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-4">
                  <div className="mb-2 text-[10px] font-bold tracking-widest text-indigo-500 uppercase">
                    Visual Composition
                  </div>
                  <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                    {scene.description}
                  </p>
                </div>
                <div className="rounded-lg border border-indigo-500/10 bg-indigo-500/5 p-4">
                  <div className="mb-2 text-[10px] font-bold tracking-widest text-indigo-500 uppercase dark:text-indigo-300">
                    Narration Script
                  </div>
                  <p className="text-sm text-[var(--foreground)] italic">"{scene.narration}"</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : hasPlan ? (
        <div className="space-y-6">
          <div className="mb-8 rounded-xl border border-indigo-500/20 bg-indigo-500/10 p-4">
            <div className="mb-1 text-[10px] font-bold tracking-widest text-indigo-500 uppercase">
              Target Audience
            </div>
            <p className="text-lg font-bold text-[var(--foreground)]">{plan!.target_audience}</p>
          </div>
          {plan!.teaching_steps.map((step) => (
            <div
              key={step.step_id}
              className="flex gap-6 rounded-xl p-4 transition-colors hover:bg-[var(--background)]/40"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--surface-border)] bg-[var(--background)] font-bold text-[var(--foreground)]">
                {step.step_id}
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-[var(--foreground)]">{step.concept}</h3>
                <div className="flex flex-col gap-1">
                  <p className="text-sm leading-relaxed text-[var(--text-muted)]">
                    <span className="font-semibold text-indigo-500 italic">Metaphor:</span>{' '}
                    {step.visual_metaphor}
                  </p>
                  <p className="mt-2 rounded-lg border border-[var(--surface-border)] bg-[var(--background)]/50 p-3 text-sm whitespace-pre-wrap text-[var(--text-muted)]">
                    <span className="mb-1 block text-[10px] font-bold text-indigo-500 opacity-60">
                      NARRATION
                    </span>
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
