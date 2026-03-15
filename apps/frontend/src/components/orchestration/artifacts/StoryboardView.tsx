import { motion } from 'framer-motion';
import { Video } from 'lucide-react';
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
        message={isQueued ? 'Queued' : 'Visual Deliberation'}
        submessage={isQueued ? 'Awaiting curriculum finalization...' : 'Architecting scenes...'}
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.99 }}
      animate={{ opacity: 1, scale: 1 }}
      className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    >
      {storyboard.scenes.map((scene, idx) => (
        <ArtifactCard 
          key={scene.scene_id} 
          delay={idx * 0.05}
          className="hover:border-council-active/50"
        >
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-micro font-bold tracking-[0.1em] text-text-muted opacity-50 uppercase">
              S{scene.scene_id}
            </span>
            <Video className="h-2.5 w-2.5 text-text-muted opacity-20" />
          </div>
          <h4 className="mb-2 line-clamp-1 text-mini font-bold text-foreground uppercase tracking-tight">
            {scene.title}
          </h4>
          <div className="space-y-2">
            <div>
              <ArtifactBadge variant="completed">Script</ArtifactBadge>
              <p className="line-clamp-2 text-tiny leading-tight text-text-muted">
                {scene.description}
              </p>
            </div>
            <div>
              <ArtifactBadge variant="active">Visual</ArtifactBadge>
              <p className="line-clamp-2 text-tiny leading-tight text-text-muted italic opacity-60">
                {(scene as any).visual_prompt || scene.narration || 'Dynamic generation...'}
              </p>
            </div>
          </div>
        </ArtifactCard>
      ))}
    </motion.div>
  );
}
