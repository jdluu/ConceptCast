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
    <div className="relative space-y-8 pl-6 before:absolute before:top-2 before:bottom-2 before:left-[11px] before:w-px before:border-l before:border-dashed before:border-indigo-500/30 before:bg-gradient-to-b before:from-indigo-500/50 before:via-indigo-500/20 before:to-transparent">
      {plan.teaching_steps.map((step) => (
        <motion.div
          key={step.step_id}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="relative"
        >
          <div className="absolute top-1 -left-[31px] z-10 flex h-6 w-6 items-center justify-center rounded-lg border-2 border-[var(--surface)] bg-indigo-600 text-[10px] font-bold text-white shadow-md shadow-indigo-600/20">
            {step.step_id}
          </div>
          <div className="group/step rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-4 shadow-sm transition-all hover:border-indigo-500/30">
            <div className="mb-2 flex items-start justify-between gap-4">
              <h3 className="text-sm font-bold text-[var(--foreground)] transition-colors group-hover/step:text-indigo-600 dark:group-hover/step:text-indigo-400">
                {step.concept}
              </h3>
              <Lightbulb className="h-4 w-4 shrink-0 text-amber-400/50 transition-colors group-hover/step:text-amber-400" />
            </div>
            <p className="border-l-2 border-indigo-500/10 pl-3 text-xs leading-relaxed text-[var(--text-muted)] italic opacity-80">
              {step.visual_metaphor}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
