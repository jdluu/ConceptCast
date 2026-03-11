import { Video, Layers, Type } from 'lucide-react';
import type { Storyboard } from '@/lib/api/client';
import { ArtifactCard, ArtifactBadge } from './artifacts/ArtifactCommon';

interface SceneGalleryProps {
  /** The storyboard containing scene definitions. */
  storyboard: Storyboard;
}

/**
 * Renders storyboard scenes as a responsive card grid with thumbnails,
 * descriptions, and optional narration text.
 * 
 * Uses the unified ArtifactCard pattern for visual consistency across the app.
 */
export function SceneGallery({ storyboard }: SceneGalleryProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {storyboard.scenes.map((scene, idx) => (
        <ArtifactCard 
          key={scene.scene_id} 
          delay={idx * 0.05}
          className="group/scene p-0 hover:border-council-active/50"
        >
          {/* Thumbnail / Header Area */}
          <div className="relative flex aspect-video items-center justify-center border-b border-surface-border bg-surface">
            <Video className="h-8 w-8 text-council-active/20 transition-all duration-500 group-hover/scene:scale-110 group-hover/scene:text-council-active/40" />
            <div className="absolute top-3 left-3 rounded bg-black/50 px-2 py-0.5 text-micro font-bold tracking-widest text-white uppercase backdrop-blur-sm">
              Scene {scene.scene_id}
            </div>
          </div>

          {/* Content Area */}
          <div className="space-y-4 p-4">
            <h4 className="text-mini font-bold text-foreground uppercase tracking-tight transition-colors group-hover/scene:text-council-active">
              {scene.title}
            </h4>

            <div className="space-y-3">
              <div className="space-y-1">
                <ArtifactBadge variant="completed">Visual Direction</ArtifactBadge>
                <div className="flex gap-2">
                  <Layers className="mt-0.5 h-3 w-3 shrink-0 text-council-completed" />
                  <p className="line-clamp-2 text-tiny leading-relaxed text-text-muted">
                    {scene.description}
                  </p>
                </div>
              </div>
              
              {scene.narration && (
                <div className="space-y-1">
                  <ArtifactBadge variant="active">Narration Script</ArtifactBadge>
                  <div className="flex gap-2 rounded-lg border border-council-active/10 bg-council-active/[0.03] p-3 transition-colors group-hover/scene:bg-council-active/[0.06]">
                    <Type className="mt-0.5 h-3 w-3 shrink-0 text-council-active/60" />
                    <p className="line-clamp-3 text-tiny text-text-muted italic leading-snug">
                      "{scene.narration}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </ArtifactCard>
      ))}
    </div>
  );
}
