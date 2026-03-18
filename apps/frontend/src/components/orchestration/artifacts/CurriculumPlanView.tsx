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
        submessage={
          isQueued ? 'Awaiting council initialization...' : 'Architecting teaching steps...'
        }
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
          className="group hover:border-council-active/40 relative flex-col items-start gap-3 p-4"
        >
          <div className="border-council-active/20 bg-council-active/10 text-council-active group-hover:bg-council-active flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border text-xs font-bold shadow-sm transition-all group-hover:text-white">
            {step.step_id}
          </div>
          <div className="w-full flex-1 space-y-1 overflow-hidden">
            <h3 className="text-foreground group-hover:text-council-active truncate text-[11px] font-bold tracking-tight uppercase transition-colors">
              {step.concept}
            </h3>
            <p className="text-micro text-text-muted line-clamp-2 leading-tight italic opacity-70">
              {step.visual_metaphor}
            </p>
          </div>
        </ArtifactCard>
      ))}
      {plan.teaching_steps.length > 10 && (
        <div className="mt-4 sm:col-span-2 lg:col-span-5">
          <ArtifactAction onClick={onViewFull}>
            Explore All {plan.teaching_steps.length} Pedagogical Steps
          </ArtifactAction>
        </div>
      )}
    </motion.div>
  );
}
