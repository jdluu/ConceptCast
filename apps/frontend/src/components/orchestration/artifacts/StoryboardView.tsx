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
        submessage={isQueued ? 'Waiting for pedagogical structure...' : 'Designing cinematic sequences...'}
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
          className="group hover:border-council-active/50 p-5 gap-4"
        >
          <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-1">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-council-active/10 text-council-active ring-1 ring-council-active/20">
                <Film className="h-3 w-3" />
              </div>
              <span className="text-[10px] font-bold tracking-[0.2em] text-text-muted uppercase">
                SCENE_{scene.scene_id}
              </span>
            </div>
            <Video className="h-3 w-3 text-text-muted opacity-30" />
          </div>
          
          <h4 className="line-clamp-1 text-sm font-bold text-foreground uppercase tracking-tight group-hover:text-council-active transition-colors">
            {scene.title}
          </h4>
          
          <div className="space-y-4">
            <div className="space-y-1.5">
              <ArtifactBadge variant="completed">Script</ArtifactBadge>
              <p className="line-clamp-3 text-xs leading-relaxed text-text-muted font-medium italic">
                "{scene.narration}"
              </p>
            </div>
            
            <div className="space-y-1.5 pt-2 border-t border-surface-border/50">
              <ArtifactBadge variant="active">Visual Composition</ArtifactBadge>
              <p className="line-clamp-3 text-xs leading-relaxed text-text-muted">
                {scene.description}
              </p>
            </div>
          </div>
        </ArtifactCard>
      ))}
    </motion.div>
  );
}
