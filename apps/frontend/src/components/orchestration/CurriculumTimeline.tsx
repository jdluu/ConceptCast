import { motion } from 'framer-motion';
import { Lightbulb } from 'lucide-react';
import type { CurriculumPlan } from '@/lib/api/client';

interface CurriculumTimelineProps {
    /** The curriculum plan containing teaching steps. */
    plan: CurriculumPlan;
}

/**
 * Renders the teaching steps as a vertical timeline with animated entries.
 *
 * @param {CurriculumTimelineProps} props - Component properties.
 * @returns {JSX.Element} The rendered curriculum timeline.
 */
export function CurriculumTimeline({ plan }: CurriculumTimelineProps) {
    return (
        <div className="relative pl-6 space-y-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-gradient-to-b before:from-indigo-500/50 before:via-indigo-500/20 before:to-transparent before:border-l before:border-dashed before:border-indigo-500/30">
            {plan.teaching_steps.map((step) => (
                <motion.div 
                    key={step.step_id}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="relative"
                >
                    <div className="absolute -left-[31px] top-1 w-6 h-6 rounded-lg bg-indigo-600 border-2 border-[var(--surface)] text-white flex items-center justify-center text-[10px] font-bold shadow-md shadow-indigo-600/20 z-10">
                        {step.step_id}
                    </div>
                    <div className="p-4 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] hover:border-indigo-500/30 transition-all group/step shadow-sm">
                        <div className="flex items-start justify-between gap-4 mb-2">
                            <h3 className="font-bold text-sm text-[var(--foreground)] group-hover/step:text-indigo-600 dark:group-hover/step:text-indigo-400 transition-colors">
                                {step.concept}
                            </h3>
                            <Lightbulb className="w-4 h-4 text-amber-400/50 group-hover/step:text-amber-400 transition-colors shrink-0" />
                        </div>
                        <p className="text-xs text-[var(--text-muted)] leading-relaxed italic opacity-80 border-l-2 border-indigo-500/10 pl-3">
                            {step.visual_metaphor}
                        </p>
                    </div>
                </motion.div>
            ))}
        </div>
    );
}
