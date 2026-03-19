import { AnimatePresence } from 'motion/react';
import * as m from 'motion/react-m';
import { Video } from 'lucide-react';
import { CurriculumPlan, Storyboard } from '@/lib/api/client';
import {
  ArtifactCard,
  ArtifactPlaceholder,
  ArtifactBadge,
  ArtifactAction,
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
    <m.div
      layout
      className="border-surface-border bg-surface overflow-hidden rounded-2xl border shadow-xl"
    >
      <div className="border-surface-border bg-surface/50 flex items-center justify-between border-b px-4 py-3">
        <div className="flex items-center gap-3">
          <m.span
            animate={{ opacity: [0.4, 1, 0.4] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="bg-council-active h-2 w-2 rounded-full"
          />
          <span className="text-foreground text-sm font-bold tracking-wider uppercase">
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
            className="text-tiny text-council-active hover:bg-council-active/10 rounded px-2 py-1 font-bold tracking-widest uppercase transition-colors"
          >
            View Full
          </button>
        )}
        {isRendering && (
          <span className="text-council-active font-mono text-xs">
            {Math.round(renderProgress)}% COMPLETE
          </span>
        )}
      </div>

      <div className="custom-scrollbar overflow-y-auto p-4">
        <AnimatePresence mode="wait">
          {hasStoryboard ? (
            <m.div
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
                    <span className="text-nano text-text-muted font-bold tracking-widest uppercase">
                      Scene {scene.scene_id}
                    </span>
                    <Video className="text-text-muted h-2.5 w-2.5 opacity-30" />
                  </div>
                  <h4 className="text-tiny text-foreground mb-2 line-clamp-1 font-bold tracking-tight uppercase">
                    {scene.title}
                  </h4>
                  <div className="space-y-2">
                    <div>
                      <ArtifactBadge variant="completed">Narration</ArtifactBadge>
                      <p className="text-micro text-text-muted line-clamp-3 leading-snug">
                        {scene.description}
                      </p>
                    </div>
                    <div>
                      <ArtifactBadge variant="active">Visual Prompt</ArtifactBadge>
                      <p className="text-nano text-text-muted line-clamp-2 leading-tight italic opacity-70">
                        {(scene as any).visual_prompt ||
                          scene.narration ||
                          'Dynamic Manim visualization...'}
                      </p>
                    </div>
                  </div>
                </ArtifactCard>
              ))}
            </m.div>
          ) : hasPlan ? (
            <m.div
              key="plan"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-4"
            >
              {plan!.teaching_steps.slice(0, 5).map((step, idx) => (
                <ArtifactCard
                  key={step.step_id}
                  delay={idx * 0.05}
                  className="hover:border-council-active/30 flex-row items-center gap-5"
                >
                  <span className="border-council-active/20 bg-council-active/10 text-council-active flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border text-sm font-bold">
                    {step.step_id}
                  </span>
                  <div>
                    <h3 className="text-foreground text-sm font-bold tracking-tight">
                      {step.concept}
                    </h3>
                    <p className="text-text-muted mt-1.5 line-clamp-1 text-xs italic opacity-80">
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
            </m.div>
          ) : (
            <ArtifactPlaceholder
              status="loading"
              message="Connecting to Council"
              submessage="Awaiting deliberation artifacts..."
            />
          )}
        </AnimatePresence>
      </div>
    </m.div>
  );
}
