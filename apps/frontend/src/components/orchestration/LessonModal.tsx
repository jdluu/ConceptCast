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
                                <span className="px-2 py-1 bg-indigo-500 text-white text-[10px] font-bold rounded">SCENE {scene.scene_id}</span>
                                <h3 className="text-lg font-bold text-[var(--foreground)]">{scene.title}</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="p-4 rounded-lg bg-[var(--background)] border border-[var(--surface-border)]">
                                    <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-2">Visual Composition</div>
                                    <p className="text-[var(--text-muted)] text-sm leading-relaxed">{scene.description}</p>
                                </div>
                                <div className="p-4 rounded-lg bg-indigo-500/5 border border-indigo-500/10">
                                    <div className="text-[10px] font-bold text-indigo-500 dark:text-indigo-300 uppercase tracking-widest mb-2">Narration Script</div>
                                    <p className="text-sm italic text-[var(--foreground)]">"{scene.narration}"</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : hasPlan ? (
                <div className="space-y-6">
                    <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 mb-8">
                         <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-1">Target Audience</div>
                         <p className="text-[var(--foreground)] text-lg font-bold">{plan!.target_audience}</p>
                    </div>
                    {plan!.teaching_steps.map((step) => (
                        <div key={step.step_id} className="flex gap-6 p-4 rounded-xl hover:bg-[var(--background)]/40 transition-colors">
                            <div className="shrink-0 w-10 h-10 rounded-full bg-[var(--background)] flex items-center justify-center text-[var(--foreground)] font-bold border border-[var(--surface-border)]">
                                {step.step_id}
                            </div>
                            <div className="space-y-2">
                                <h3 className="text-xl font-bold text-[var(--foreground)]">{step.concept}</h3>
                                <div className="flex flex-col gap-1">
                                     <p className="text-sm text-[var(--text-muted)] leading-relaxed"><span className="text-indigo-500 font-semibold italic">Metaphor:</span> {step.visual_metaphor}</p>
                                     <p className="text-sm text-[var(--text-muted)] mt-2 p-3 bg-[var(--background)]/50 rounded-lg border border-[var(--surface-border)] whitespace-pre-wrap"><span className="text-[10px] font-bold block mb-1 text-indigo-500 opacity-60">NARRATION</span>"{step.narration}"</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : null}
        </Modal>
    );
}
