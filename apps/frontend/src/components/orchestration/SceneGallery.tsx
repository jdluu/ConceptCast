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
          className="group/scene hover:border-council-active/50 p-0"
        >
          {/* Thumbnail / Header Area */}
          <div className="border-surface-border bg-surface relative flex aspect-video items-center justify-center border-b">
            <Video className="text-council-active/20 group-hover/scene:text-council-active/40 h-8 w-8 transition-all duration-500 group-hover/scene:scale-110" />
            <div className="text-micro absolute top-3 left-3 rounded bg-black/50 px-2 py-0.5 font-bold tracking-widest text-white uppercase backdrop-blur-sm">
              Scene {scene.scene_id}
            </div>
          </div>

          {/* Content Area */}
          <div className="space-y-4 p-4">
            <h4 className="text-mini text-foreground group-hover/scene:text-council-active font-bold tracking-tight uppercase transition-colors">
              {scene.title}
            </h4>

            <div className="space-y-3">
              <div className="space-y-1">
                <ArtifactBadge variant="completed">Visual Direction</ArtifactBadge>
                <div className="flex gap-2">
                  <Layers className="text-council-completed mt-0.5 h-3 w-3 shrink-0" />
                  <p className="text-tiny text-text-muted line-clamp-2 leading-relaxed">
                    {scene.description}
                  </p>
                </div>
              </div>

              {scene.narration && (
                <div className="space-y-1">
                  <ArtifactBadge variant="active">Narration Script</ArtifactBadge>
                  <div className="border-council-active/10 bg-council-active/[0.03] group-hover/scene:bg-council-active/[0.06] flex gap-2 rounded-lg border p-3 transition-colors">
                    <Type className="text-council-active/60 mt-0.5 h-3 w-3 shrink-0" />
                    <p className="text-tiny text-text-muted line-clamp-3 leading-snug italic">
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
