import { motion } from 'framer-motion';
import { Lightbulb } from 'lucide-react';
import type { CurriculumPlan } from '@/lib/api/client';
import { ArtifactCard } from './artifacts/ArtifactCommon';

interface CurriculumTimelineProps {
  /** The curriculum plan containing teaching steps. */
  plan: CurriculumPlan;
}

/**
 * Renders the teaching steps as a vertical timeline with animated entries.
 */
export function CurriculumTimeline({ plan }: CurriculumTimelineProps) {
  return (
    <div className="before:border-council-active/30 before:from-council-active/50 before:via-council-active/20 relative space-y-8 pl-6 before:absolute before:top-2 before:bottom-2 before:left-3 before:w-px before:border-l before:border-dashed before:bg-gradient-to-b before:to-transparent">
      {plan.teaching_steps.map((step, idx) => (
        <motion.div
          key={step.step_id}
          initial={{ opacity: 0, x: -10 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: idx * 0.05 }}
          className="relative"
        >
          {/* Step Number Badge */}
          <div className="border-surface bg-council-completed text-tiny shadow-council-completed/20 absolute top-1 -left-8 z-10 flex h-6 w-6 items-center justify-center rounded-lg border-2 font-bold text-white shadow-md">
            {step.step_id}
          </div>

          <ArtifactCard className="group/step hover:border-council-active/30">
            <div className="mb-2 flex items-start justify-between gap-4">
              <h3 className="text-sm-plus text-foreground group-hover/step:text-council-active font-bold transition-colors">
                {step.concept}
              </h3>
              <Lightbulb className="text-warning/50 group-hover/step:text-warning h-4 w-4 shrink-0 transition-colors" />
            </div>
            <p className="border-council-active/10 text-mini text-text-muted border-l-2 pl-3 leading-relaxed italic opacity-80">
              {step.visual_metaphor}
            </p>
          </ArtifactCard>
        </motion.div>
      ))}
    </div>
  );
}
