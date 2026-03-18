import { motion } from 'framer-motion';
import { Video, Film } from 'lucide-react';
import { Storyboard } from '@/lib/api/client';
import { ArtifactCard, ArtifactPlaceholder, ArtifactBadge } from './ArtifactCommon';

interface StoryboardViewProps {
  storyboard: Storyboard | null;
  status: string;
}

export function StoryboardView({ storyboard, status }: StoryboardViewProps) {
  const isQueued = status === 'pending' || status === 'queued' || status === 'planning';

  if (!storyboard) {
    return (
      <ArtifactPlaceholder
        status={isQueued ? 'queued' : 'loading'}
        message={isQueued ? 'Visual Sequence Pending' : 'Visual Deliberation'}
        submessage={
          isQueued ? 'Waiting for pedagogical structure...' : 'Designing cinematic sequences...'
        }
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5"
    >
      {storyboard.scenes.map((scene, idx) => (
        <ArtifactCard
          key={scene.scene_id}
          delay={idx * 0.05}
          className="group hover:border-council-active/50 gap-4 p-5"
        >
          <div className="border-surface-border mb-1 flex items-center justify-between border-b pb-3">
            <div className="flex items-center gap-2">
              <div className="bg-council-active/10 text-council-active ring-council-active/20 flex h-6 w-6 items-center justify-center rounded-md ring-1">
                <Film className="h-3 w-3" />
              </div>
              <span className="text-text-muted text-[10px] font-bold tracking-[0.2em] uppercase">
                SCENE_{scene.scene_id}
              </span>
            </div>
            <Video className="text-text-muted h-3 w-3 opacity-30" />
          </div>

          <h4 className="text-foreground group-hover:text-council-active line-clamp-1 text-sm font-bold tracking-tight uppercase transition-colors">
            {scene.title}
          </h4>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <ArtifactBadge variant="completed">Script</ArtifactBadge>
              <p className="text-text-muted line-clamp-3 text-xs leading-relaxed font-medium italic">
                "{scene.narration}"
              </p>
            </div>

            <div className="border-surface-border/50 space-y-1.5 border-t pt-2">
              <ArtifactBadge variant="active">Visual Composition</ArtifactBadge>
              <p className="text-text-muted line-clamp-3 text-xs leading-relaxed">
                {scene.description}
              </p>
            </div>
          </div>
        </ArtifactCard>
      ))}
    </motion.div>
  );
}
