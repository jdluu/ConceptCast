import { motion, AnimatePresence } from 'framer-motion';
import { Video } from 'lucide-react';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';
import { 
  ArtifactCard, 
  ArtifactPlaceholder, 
  ArtifactBadge, 
  ArtifactAction 
} from './artifacts/ArtifactCommon';

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
      className="overflow-hidden rounded-2xl border border-surface-border bg-surface shadow-xl"
    >
      <div className="flex items-center justify-between border-b border-surface-border bg-surface/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <motion.span
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="h-2 w-2 rounded-full bg-council-active"
          />
          <span className="text-sm font-bold tracking-wider text-foreground uppercase">
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
            className="rounded px-2 py-1 text-tiny font-bold tracking-widest text-council-active uppercase transition-colors hover:bg-council-active/10"
          >
            View Full
          </button>
        )}
        {isRendering && (
          <span className="font-mono text-xs text-council-active">
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
              {storyboard.scenes.map((scene, idx) => (
                <ArtifactCard 
                  key={scene.scene_id} 
                  delay={idx * 0.05}
                  className="hover:border-council-active/50"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-nano font-bold tracking-widest text-text-muted uppercase">
                      Scene {scene.scene_id}
                    </span>
                    <Video className="h-2.5 w-2.5 text-text-muted opacity-30" />
                  </div>
                  <h4 className="mb-2 line-clamp-1 text-tiny font-bold text-foreground uppercase tracking-tight">
                    {scene.title}
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <ArtifactBadge variant="completed">Narration</ArtifactBadge>
                      <p className="line-clamp-3 text-micro leading-snug text-text-muted">
                        {scene.description}
                      </p>
                    </div>
                    <div>
                      <ArtifactBadge variant="active">Visual Prompt</ArtifactBadge>
                      <p className="line-clamp-2 text-nano leading-tight text-text-muted italic opacity-70">
                        {(scene as any).visual_prompt || scene.narration || 'Dynamic Manim visualization...'}
                      </p>
                    </div>
                  </div>
                </ArtifactCard>
              ))}
            </motion.div>
          ) : hasPlan ? (
            <motion.div
              key="plan"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-4"
            >
              {plan!.teaching_steps.slice(0, 5).map((step, idx) => (
                <ArtifactCard 
                  key={step.step_id} 
                  delay={idx * 0.05}
                  className="flex-row items-center gap-5 hover:border-council-active/30"
                >
                  <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border border-council-active/20 bg-council-active/10 text-sm font-bold text-council-active">
                    {step.step_id}
                  </span>
                  <div>
                    <h3 className="text-sm font-bold tracking-tight text-foreground">
                      {step.concept}
                    </h3>
                    <p className="mt-1.5 line-clamp-1 text-xs text-text-muted italic opacity-80">
                      {step.visual_metaphor}
                    </p>
                  </div>
                </ArtifactCard>
              ))}
              {plan!.teaching_steps.length > 5 && (
                <ArtifactAction onClick={onViewFull}>
                  View all {plan!.teaching_steps.length} steps in detail
                </ArtifactAction>
              )}
            </motion.div>
          ) : (
            <ArtifactPlaceholder 
              status="loading" 
              message="Connecting to Council" 
              submessage="Awaiting deliberation artifacts..." 
            />
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
