import * as m from 'motion/react-m';
import { Film, Maximize2, Minimize2 } from 'lucide-react';
import { Storyboard } from '@/lib/api/client';
import { ArtifactCard, ArtifactPlaceholder, ArtifactBadge } from './ArtifactCommon';
import { useState } from 'react';
import { cn } from '@/lib/utils';

interface StoryboardViewProps {
  storyboard: Storyboard | null;
  status: string;
}

export function StoryboardView({ storyboard, status }: StoryboardViewProps) {
  const [expandedSceneId, setExpandedSceneId] = useState<number | null>(null);
  const isQueued = status === 'pending' || status === 'queued' || status === 'planning';

  if (!storyboard) {
    return (
      <ArtifactPlaceholder
        status={isQueued ? 'queued' : 'loading'}
        message={isQueued ? 'Visual Sequence Pending' : 'Visual Deliberation'}
        submessage={
          isQueued ? 'Waiting for curriculum plan...' : 'Designing cinematic sequences...'
        }
      />
    );
  }

  return (
    <m.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5"
    >
      {storyboard.scenes.map((scene, idx) => {
        const isExpanded = expandedSceneId === scene.scene_id;

        return (
          <ArtifactCard
            key={scene.scene_id}
            delay={idx * 0.05}
            className={cn(
              'group hover:border-council-active/50 cursor-pointer gap-4 p-5 transition-all duration-300',
              isExpanded
                ? 'bg-background/80 border-council-active/30 col-span-1 shadow-lg sm:col-span-2 lg:col-span-5'
                : '',
            )}
            onClick={() => setExpandedSceneId(isExpanded ? null : scene.scene_id)}
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
              <div className="text-text-muted flex items-center gap-2 opacity-30 transition-opacity group-hover:opacity-100">
                {isExpanded ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
              </div>
            </div>

            <h4 className="text-foreground group-hover:text-council-active text-sm font-bold tracking-tight uppercase transition-colors">
              {scene.title}
            </h4>

            <div
              className={cn(
                'space-y-4',
                isExpanded ? 'mt-4 grid grid-cols-1 md:grid-cols-2 md:gap-6 md:space-y-0' : '',
              )}
            >
              <div className="space-y-1.5">
                <ArtifactBadge variant="completed">Script</ArtifactBadge>
                <p
                  className={cn(
                    'text-text-muted text-xs leading-relaxed font-medium italic',
                    !isExpanded && 'line-clamp-3',
                  )}
                >
                  "{scene.narration}"
                </p>
              </div>

              <div
                className={cn(
                  'space-y-1.5',
                  !isExpanded ? 'border-surface-border/50 border-t pt-2' : '',
                )}
              >
                <ArtifactBadge variant="active">Visual Composition</ArtifactBadge>
                <p
                  className={cn(
                    'text-text-muted text-xs leading-relaxed',
                    !isExpanded && 'line-clamp-3',
                  )}
                >
                  {scene.description}
                </p>
              </div>
            </div>
          </ArtifactCard>
        );
      })}
    </m.div>
  );
}
