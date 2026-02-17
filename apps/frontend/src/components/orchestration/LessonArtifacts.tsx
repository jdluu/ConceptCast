import { motion, AnimatePresence } from 'framer-motion';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';

interface LessonArtifactsProps {
    plan: CurriculumPlan | null;
    storyboard: Storyboard | null;
    status: string;
    renderProgress: number;
    onViewFull: () => void;
}

export function LessonArtifacts({ plan, storyboard, status, renderProgress, onViewFull }: LessonArtifactsProps) {
    const isRendering = status === 'rendering';
    const hasStoryboard = !!storyboard;
    const hasPlan = !!plan;

    return (
        <motion.div 
            layout
            className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-xl"
        >
            <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--surface-border)] bg-[var(--surface)]/50">
                <div className="flex items-center gap-3">
                    <motion.span 
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 2, repeat: Infinity }}
                        className="w-2 h-2 rounded-full bg-indigo-500" 
                    />
                    <span className="text-sm font-bold text-[var(--foreground)] tracking-wider uppercase">
                        {isRendering ? 'Rendering Preview' : hasStoryboard ? 'Visual Storyboard' : 'Curriculum Plan'}
                    </span>
                </div>
                {(hasPlan || hasStoryboard) && (
                    <button 
                        onClick={onViewFull}
                        className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 uppercase tracking-widest px-2 py-1 rounded hover:bg-indigo-500/10 transition-colors"
                    >
                        View Full
                    </button>
                )}
                {isRendering && (
                    <span className="text-xs font-mono text-indigo-400">
                        {Math.round(renderProgress)}% COMPLETE
                    </span>
                )}
            </div>

            <div className="p-6 overflow-y-auto custom-scrollbar">
                <AnimatePresence mode="wait">
                    {hasStoryboard ? (
                        <motion.div 
                            key="storyboard"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                        >
                            {storyboard.scenes.slice(0, 4).map((scene) => (
                                <div key={scene.scene_id} className="p-5 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] hover:border-indigo-500/50 transition-all shadow-sm group/scene">
                                    <div className="text-[10px] font-bold text-[var(--text-muted)] mb-2 tracking-widest uppercase">SCENE {scene.scene_id}</div>
                                    <h4 className="text-[var(--foreground)] text-sm font-bold mb-2 line-clamp-1 group-hover/scene:text-indigo-600 dark:group-hover/scene:text-indigo-400 transition-colors uppercase tracking-tight">{scene.title}</h4>
                                    <p className="text-[var(--text-muted)] text-xs line-clamp-2 leading-relaxed">{scene.description}</p>
                                </div>
                            ))}
                            {storyboard.scenes.length > 4 && (
                                <button 
                                    onClick={onViewFull}
                                    className="col-span-full py-4 border-2 border-dashed border-[var(--surface-border)] rounded-xl text-[var(--text-muted)] text-xs font-bold uppercase tracking-widest hover:bg-[var(--surface)] hover:text-indigo-500 transition-all active:scale-[0.99]"
                                >
                                    + {storyboard.scenes.length - 4} more scenes. View Full Storyboard.
                                </button>
                            )}
                        </motion.div>
                    ) : hasPlan ? (
                        <motion.div 
                            key="plan"
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="space-y-4"
                        >
                            {plan!.teaching_steps.slice(0, 5).map((step) => (
                                <div key={step.step_id} className="flex gap-5 p-4 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] shadow-sm hover:border-indigo-500/30 transition-all">
                                    <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm border border-indigo-500/20">
                                        {step.step_id}
                                    </span>
                                    <div>
                                        <h3 className="text-[var(--foreground)] text-sm font-bold tracking-tight">{step.concept}</h3>
                                        <p className="text-[var(--text-muted)] text-xs mt-1.5 line-clamp-1 italic italic opacity-80">
                                            {step.visual_metaphor}
                                        </p>
                                    </div>
                                </div>
                            ))}
                            {plan!.teaching_steps.length > 5 && (
                                <button 
                                    onClick={onViewFull}
                                    className="w-full py-3 text-[var(--text-muted)] text-xs font-bold uppercase tracking-widest hover:text-indigo-500 transition-colors"
                                >
                                    View all {plan!.teaching_steps.length} steps in detail
                                </button>
                            )}
                        </motion.div>
                    ) : (
                        <motion.div 
                            key="loading"
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="h-full flex flex-col items-center justify-center text-[var(--text-muted)] space-y-4 py-24"
                        >
                            <div className="w-10 h-10 rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 animate-spin shadow-sm" />
                            <p className="text-sm font-medium italic opacity-60">Connecting to Council...</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
