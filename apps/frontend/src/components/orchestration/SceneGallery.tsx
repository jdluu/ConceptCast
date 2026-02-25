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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {storyboard.scenes.map((scene) => (
                <motion.div 
                    key={scene.scene_id}
                    whileHover={{ scale: 1.01 }}
                    className="flex flex-col rounded-xl bg-[var(--background)] border border-[var(--surface-border)] overflow-hidden hover:border-indigo-500/30 transition-all shadow-sm group/scene"
                >
                    <div className="aspect-video bg-[var(--surface)] flex items-center justify-center relative border-b border-[var(--surface-border)]">
                        <Video className="w-8 h-8 text-indigo-500/20 group-hover/scene:scale-110 group-hover/scene:text-indigo-500/40 transition-all duration-500" />
                        <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/50 text-[9px] font-bold text-white uppercase tracking-widest backdrop-blur-sm">
                            Scene {scene.scene_id}
                        </div>
                    </div>
                    
                    <div className="p-4 space-y-3">
                        <h4 className="text-xs font-bold text-[var(--foreground)] uppercase group-hover/scene:text-indigo-500 transition-colors">
                            {scene.title}
                        </h4>
                        
                        <div className="space-y-2">
                            <div className="flex gap-2">
                                <Layers className="w-3 h-3 text-indigo-500 shrink-0 mt-0.5" />
                                <p className="text-[11px] text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                                    {scene.description}
                                </p>
                            </div>
                            {scene.narration && (
                                <div className="flex gap-2 p-2 rounded bg-indigo-500/[0.03] border border-indigo-500/5">
                                    <Type className="w-3 h-3 text-indigo-400/60 shrink-0 mt-0.5" />
                                    <p className="text-[10px] text-[var(--text-muted)] italic line-clamp-2 opacity-70">
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
