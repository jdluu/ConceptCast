import { motion } from 'framer-motion';
import { CurriculumPlan } from '@/lib/api/client';

interface CurriculumPlanViewProps {
  plan: CurriculumPlan | null;
  status: string;
  onViewFull: () => void;
}

export function CurriculumPlanView({ plan, status, onViewFull }: CurriculumPlanViewProps) {
  const isQueued = status === 'pending' || status === 'queued';

  if (!plan) {
    if (isQueued) {
      return (
        <div className="flex h-32 flex-col items-center justify-center space-y-2 rounded-xl border border-dashed border-[var(--surface-border)] py-12 opacity-40">
          <p className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">Queued</p>
          <p className="text-[9px] text-[var(--text-muted)] italic">Awaiting pedagogical initialization...</p>
        </div>
      );
    }

    return (
      <div className="flex h-32 flex-col items-center justify-center space-y-3 py-12 text-[var(--text-muted)]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 shadow-sm" />
        <p className="text-[11px] font-medium italic opacity-60">Architecting pedagogy...</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="grid grid-cols-1 gap-2 sm:grid-cols-2"
    >
      {plan.teaching_steps.slice(0, 10).map((step) => (
        <div
          key={step.step_id}
          className="flex items-center gap-3 rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-3 shadow-sm transition-all hover:border-indigo-500/30"
        >
          <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md border border-indigo-500/20 bg-indigo-500/10 text-[11px] font-bold text-indigo-500 dark:text-indigo-400">
            {step.step_id}
          </span>
          <div className="flex-1 overflow-hidden">
            <h3 className="text-[11px] font-bold tracking-tight text-[var(--foreground)] truncate">
              {step.concept}
            </h3>
            <p className="line-clamp-1 text-[10px] text-[var(--text-muted)] italic opacity-70">
              {step.visual_metaphor}
            </p>
          </div>
        </div>
      ))}
      {plan.teaching_steps.length > 10 && (
        <button
          onClick={onViewFull}
          className="w-full py-2 text-[9px] font-bold tracking-[0.2em] text-[var(--text-muted)] uppercase transition-colors hover:text-indigo-500"
        >
          Explore All {plan.teaching_steps.length} Steps
        </button>
      )}
    </motion.div>
  );
}
