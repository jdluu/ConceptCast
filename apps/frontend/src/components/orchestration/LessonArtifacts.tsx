import { motion, AnimatePresence } from 'framer-motion';
import { Video } from 'lucide-react';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';

interface LessonArtifactsProps {
  plan: CurriculumPlan | null;
  storyboard: Storyboard | null;
  status: string;
  renderProgress: number;
  onViewFull: () => void;
}

export function LessonArtifacts({
  plan,
  storyboard,
  status,
  renderProgress,
  onViewFull,
}: LessonArtifactsProps) {
  const isRendering = status === 'rendering';
  const hasStoryboard = !!storyboard;
  const hasPlan = !!plan;

  return (
    <motion.div
      layout
      className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] shadow-xl"
    >
      <div className="flex items-center justify-between border-b border-[var(--surface-border)] bg-[var(--surface)]/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <motion.span
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="h-2 w-2 rounded-full bg-indigo-500"
          />
          <span className="text-sm font-bold tracking-wider text-[var(--foreground)] uppercase">
            {isRendering
              ? 'Rendering Preview'
              : hasStoryboard
                ? 'Visual Storyboard'
                : 'Curriculum Plan'}
          </span>
        </div>
        {(hasPlan || hasStoryboard) && (
          <button
            onClick={onViewFull}
            className="rounded px-2 py-1 text-[10px] font-bold tracking-widest text-indigo-400 uppercase transition-colors hover:bg-indigo-500/10 hover:text-indigo-300"
          >
            View Full
          </button>
        )}
        {isRendering && (
          <span className="font-mono text-xs text-indigo-400">
            {Math.round(renderProgress)}% COMPLETE
          </span>
        )}
      </div>

      <div className="custom-scrollbar overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {hasStoryboard ? (
            <motion.div
              key="storyboard"
              initial={{ opacity: 0, scale: 0.99 }}
              animate={{ opacity: 1, scale: 1 }}
              className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5"
            >
              {storyboard.scenes.map((scene) => (
                <div
                  key={scene.scene_id}
                  className="flex flex-col rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-3 shadow-[var(--card-shadow)] transition-all hover:border-[var(--council-active)]/50"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-[8px] font-bold tracking-widest text-[var(--text-muted)] uppercase">
                      Scene {scene.scene_id}
                    </span>
                    <Video className="h-2.5 w-2.5 text-[var(--text-muted)] opacity-30" />
                  </div>
                  <h4 className="mb-2 line-clamp-1 text-[10px] font-bold text-[var(--foreground)] uppercase tracking-tight">
                    {scene.title}
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <span className="mb-0.5 block text-[8px] font-bold text-[var(--council-completed)] uppercase tracking-tighter">
                        Narration
                      </span>
                      <p className="line-clamp-3 text-[9px] leading-snug text-[var(--text-muted)]">
                        {scene.description}
                      </p>
                    </div>
                    <div>
                      <span className="mb-0.5 block text-[8px] font-bold text-[var(--council-active)] uppercase tracking-tighter">
                        Visual Prompt
                      </span>
                      <p className="line-clamp-2 text-[8px] leading-tight text-[var(--text-muted)] italic opacity-70">
                        {(scene as any).visual_prompt || scene.narration || 'Dynamic Manim visualization...'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </motion.div>
          ) : hasPlan ? (
            <motion.div
              key="plan"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-4"
            >
              {plan!.teaching_steps.slice(0, 5).map((step) => (
                <div
                  key={step.step_id}
                  className="flex gap-5 rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-4 shadow-sm transition-all hover:border-indigo-500/30"
                >
                  <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-indigo-500/20 bg-indigo-500/10 text-sm font-bold text-indigo-600 dark:text-indigo-400">
                    {step.step_id}
                  </span>
                  <div>
                    <h3 className="text-sm font-bold tracking-tight text-[var(--foreground)]">
                      {step.concept}
                    </h3>
                    <p className="mt-1.5 line-clamp-1 text-xs text-[var(--text-muted)] italic opacity-80">
                      {step.visual_metaphor}
                    </p>
                  </div>
                </div>
              ))}
              {plan!.teaching_steps.length > 5 && (
                <button
                  onClick={onViewFull}
                  className="w-full py-3 text-xs font-bold tracking-widest text-[var(--text-muted)] uppercase transition-colors hover:text-indigo-500"
                >
                  View all {plan!.teaching_steps.length} steps in detail
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="loading"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex h-full flex-col items-center justify-center space-y-4 py-24 text-[var(--text-muted)]"
            >
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 shadow-sm" />
              <p className="text-sm font-medium italic opacity-60">Connecting to Council...</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
