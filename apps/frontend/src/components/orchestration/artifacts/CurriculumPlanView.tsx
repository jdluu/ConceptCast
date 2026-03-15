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
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      {plan.teaching_steps.slice(0, 12).map((step, idx) => (
        <ArtifactCard 
          key={step.step_id} 
          delay={idx * 0.05}
          className="group relative flex-row items-start gap-5 p-5 hover:border-council-active/40"
        >
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl border border-council-active/20 bg-council-active/10 text-sm font-bold text-council-active transition-all group-hover:bg-council-active group-hover:text-white shadow-sm ring-1 ring-council-active/10 group-hover:scale-110">
            {step.step_id}
          </div>
          <div className="flex-1 space-y-2 overflow-hidden">
            <h3 className="text-sm font-bold tracking-tight text-foreground uppercase opacity-90 group-hover:opacity-100">
              {step.concept}
            </h3>
            <div className="space-y-1.5">
              <div className="flex items-start gap-2">
                <span className="text-[10px] font-bold text-council-active/60 uppercase tracking-widest mt-0.5">Visual:</span>
                <p className="text-xs text-text-muted italic leading-relaxed">
                  {step.visual_metaphor}
                </p>
              </div>
              <p className="text-tiny text-text-muted/70 line-clamp-2 leading-relaxed">
                {step.narration}
              </p>
            </div>
          </div>
        </ArtifactCard>
      ))}
      {plan.teaching_steps.length > 12 && (
        <div className="sm:col-span-2 xl:col-span-3 mt-4">
          <ArtifactAction onClick={onViewFull}>
            Explore All {plan.teaching_steps.length} Pedagogical Steps
          </ArtifactAction>
        </div>
      )}
    </motion.div>
  );
}
