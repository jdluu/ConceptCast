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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5"
    >
      {plan.teaching_steps.slice(0, 10).map((step, idx) => (
        <ArtifactCard 
          key={step.step_id} 
          delay={idx * 0.05}
          className="group relative flex-col items-start gap-3 p-4 hover:border-council-active/40"
        >
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-council-active/20 bg-council-active/10 text-xs font-bold text-council-active transition-all group-hover:bg-council-active group-hover:text-white shadow-sm">
            {step.step_id}
          </div>
          <div className="flex-1 space-y-1 overflow-hidden w-full">
            <h3 className="text-[11px] font-bold tracking-tight text-foreground uppercase truncate group-hover:text-council-active transition-colors">
              {step.concept}
            </h3>
            <p className="text-micro text-text-muted italic line-clamp-2 leading-tight opacity-70">
              {step.visual_metaphor}
            </p>
          </div>
        </ArtifactCard>
      ))}
      {plan.teaching_steps.length > 10 && (
        <div className="sm:col-span-2 lg:col-span-5 mt-4">
          <ArtifactAction onClick={onViewFull}>
            Explore All {plan.teaching_steps.length} Pedagogical Steps
          </ArtifactAction>
        </div>
      )}
    </motion.div>
  );
}
