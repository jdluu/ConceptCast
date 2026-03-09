import { motion } from 'framer-motion';
import { Video, Layers, Type } from 'lucide-react';
import type { Storyboard } from '@/lib/api/client';

interface SceneGalleryProps {
  /** The storyboard containing scene definitions. */
  storyboard: Storyboard;
}

/**
 * Renders storyboard scenes as a responsive card grid with thumbnails,
 * descriptions, and optional narration text.
 *
 * @param {SceneGalleryProps} props - Component properties.
 * @returns {JSX.Element} The rendered scene gallery.
 */
export function SceneGallery({ storyboard }: SceneGalleryProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {storyboard.scenes.map((scene) => (
        <motion.div
          key={scene.scene_id}
          whileHover={{ scale: 1.01 }}
          className="group/scene flex flex-col overflow-hidden rounded-xl border border-[var(--surface-border)] bg-[var(--background)] shadow-sm transition-all hover:border-indigo-500/30"
        >
          <div className="relative flex aspect-video items-center justify-center border-b border-[var(--surface-border)] bg-[var(--surface)]">
            <Video className="h-8 w-8 text-indigo-500/20 transition-all duration-500 group-hover/scene:scale-110 group-hover/scene:text-indigo-500/40" />
            <div className="absolute top-3 left-3 rounded bg-black/50 px-2 py-0.5 text-[9px] font-bold tracking-widest text-white uppercase backdrop-blur-sm">
              Scene {scene.scene_id}
            </div>
          </div>

          <div className="space-y-3 p-4">
            <h4 className="text-xs font-bold text-[var(--foreground)] uppercase transition-colors group-hover/scene:text-indigo-500">
              {scene.title}
            </h4>

            <div className="space-y-2">
              <div className="flex gap-2">
                <Layers className="mt-0.5 h-3 w-3 shrink-0 text-indigo-500" />
                <p className="line-clamp-2 text-[11px] leading-relaxed text-[var(--text-muted)]">
                  {scene.description}
                </p>
              </div>
              {scene.narration && (
                <div className="flex gap-2 rounded border border-indigo-500/5 bg-indigo-500/[0.03] p-2">
                  <Type className="mt-0.5 h-3 w-3 shrink-0 text-indigo-400/60" />
                  <p className="line-clamp-2 text-[10px] text-[var(--text-muted)] italic opacity-70">
                    "{scene.narration}"
                  </p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
