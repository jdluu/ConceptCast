import { motion } from 'framer-motion';
import { CurriculumPlan } from '@/lib/api/client';
import { ArtifactCard, ArtifactPlaceholder, ArtifactAction } from './ArtifactCommon';

interface CurriculumPlanViewProps {
  plan: CurriculumPlan | null;
  status: string;
  onViewFull: () => void;
}

export function CurriculumPlanView({ plan, status, onViewFull }: CurriculumPlanViewProps) {
  const isQueued = status === 'pending' || status === 'queued';

  if (!plan) {
    return (
      <ArtifactPlaceholder 
        status={isQueued ? 'queued' : 'loading'} 
        message={isQueued ? 'Queued' : 'Pedagogy Design'}
        submessage={isQueued ? 'Awaiting council initialization...' : 'Architecting teaching steps...'}
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3"
    >
      {plan.teaching_steps.slice(0, 12).map((step, idx) => (
        <ArtifactCard 
          key={step.step_id} 
          delay={idx * 0.05}
          className="flex-row items-center gap-4 group hover:border-council-active/40"
        >
          <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-council-active/20 bg-council-active/10 text-xs font-bold text-council-active transition-colors group-hover:bg-council-active group-hover:text-white">
            {step.step_id}
          </span>
          <div className="flex-1 overflow-hidden">
            <h3 className="text-[11px] font-bold tracking-tight text-foreground truncate uppercase opacity-90 group-hover:opacity-100">
              {step.concept}
            </h3>
            <p className="line-clamp-1 text-tiny text-text-muted italic opacity-60 mt-0.5">
              {step.visual_metaphor}
            </p>
          </div>
        </ArtifactCard>
      ))}
      {plan.teaching_steps.length > 12 && (
        <div className="sm:col-span-2 lg:col-span-3 mt-2">
          <ArtifactAction onClick={onViewFull}>
            Explore All {plan.teaching_steps.length} Steps
          </ArtifactAction>
        </div>
      )}
    </motion.div>
  );
}
