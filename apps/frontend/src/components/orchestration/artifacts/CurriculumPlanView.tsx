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
      className="grid grid-cols-1 gap-2 sm:grid-cols-2"
    >
      {plan.teaching_steps.slice(0, 10).map((step, idx) => (
        <ArtifactCard 
          key={step.step_id} 
          delay={idx * 0.05}
          className="flex-row items-center gap-3"
        >
          <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-council-active/20 bg-council-active/10 text-mini font-bold text-council-active">
            {step.step_id}
          </span>
          <div className="flex-1 overflow-hidden">
            <h3 className="text-mini font-bold tracking-tight text-foreground truncate">
              {step.concept}
            </h3>
            <p className="line-clamp-1 text-tiny text-text-muted italic opacity-70">
              {step.visual_metaphor}
            </p>
          </div>
        </ArtifactCard>
      ))}
      {plan.teaching_steps.length > 10 && (
        <div className="sm:col-span-2 mt-2">
          <ArtifactAction onClick={onViewFull}>
            Explore All {plan.teaching_steps.length} Steps
          </ArtifactAction>
        </div>
      )}
    </motion.div>
  );
}
