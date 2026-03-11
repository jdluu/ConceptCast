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
    <div className="relative space-y-8 pl-6 before:absolute before:top-2 before:bottom-2 before:left-3 before:w-px before:border-l before:border-dashed before:border-council-active/30 before:bg-gradient-to-b before:from-council-active/50 before:via-council-active/20 before:to-transparent">
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
          <div className="absolute top-1 -left-8 z-10 flex h-6 w-6 items-center justify-center rounded-lg border-2 border-surface bg-council-completed text-tiny font-bold text-white shadow-md shadow-council-completed/20">
            {step.step_id}
          </div>
          
          <ArtifactCard className="group/step hover:border-council-active/30">
            <div className="mb-2 flex items-start justify-between gap-4">
              <h3 className="text-sm-plus font-bold text-foreground transition-colors group-hover/step:text-council-active">
                {step.concept}
              </h3>
              <Lightbulb className="h-4 w-4 shrink-0 text-warning/50 transition-colors group-hover/step:text-warning" />
            </div>
            <p className="border-l-2 border-council-active/10 pl-3 text-mini leading-relaxed text-text-muted italic opacity-80">
              {step.visual_metaphor}
            </p>
          </ArtifactCard>
        </motion.div>
      ))}
    </div>
  );
}
