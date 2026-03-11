import { motion } from 'framer-motion';
import { Video } from 'lucide-react';
import { Storyboard } from '@/lib/api/client';

interface StoryboardViewProps {
  storyboard: Storyboard | null;
  status: string;
}

export function StoryboardView({ storyboard, status }: StoryboardViewProps) {
  const isQueued = status === 'pending' || status === 'queued' || status === 'planning';

  if (!storyboard) {
    if (isQueued) {
      return (
        <div className="flex h-32 flex-col items-center justify-center space-y-2 rounded-xl border border-dashed border-[var(--surface-border)] py-12 opacity-40">
          <p className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">Queued</p>
          <p className="text-[9px] text-[var(--text-muted)] italic">Awaiting curriculum finalization...</p>
        </div>
      );
    }

    return (
      <div className="flex h-32 flex-col items-center justify-center space-y-3 py-12 text-[var(--text-muted)]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--surface-border)] border-t-indigo-500 shadow-sm" />
        <p className="text-[11px] font-medium italic opacity-60">Awaiting visual deliberation...</p>
      </div>
    );
  }

  const totalScenes = storyboard.scenes.length;
  // Calculate balanced columns for desktop (max 2 rows if possible, cap at 6)
  const balancedCols = Math.min(6, Math.ceil(totalScenes / 2));

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.99 }}
      animate={{ opacity: 1, scale: 1 }}
      className="grid gap-2 grid-cols-2 sm:grid-cols-3"
      style={{ 
        gridTemplateColumns: `repeat(${balancedCols}, minmax(0, 1fr))` 
      }}
    >
      {storyboard.scenes.map((scene) => (
        <div
          key={scene.scene_id}
          className="flex flex-col rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-3 shadow-sm transition-all hover:border-[var(--council-active)]/50"
        >
          <div className="mb-1.5 flex items-center justify-between">
            <span className="text-[9px] font-bold tracking-[0.1em] text-[var(--text-muted)] opacity-50 uppercase">
              S{scene.scene_id}
            </span>
            <Video className="h-2.5 w-2.5 text-[var(--text-muted)] opacity-20" />
          </div>
          <h4 className="mb-2 line-clamp-1 text-[11px] font-bold text-[var(--foreground)] uppercase tracking-tight">
            {scene.title}
          </h4>
          <div className="space-y-2">
            <div>
              <span className="mb-0.5 block text-[8px] font-bold text-[var(--council-completed)] uppercase tracking-widest opacity-70">
                Script
              </span>
              <p className="line-clamp-2 text-[10px] leading-tight text-[var(--text-muted)]">
                {scene.description}
              </p>
            </div>
            <div>
              <span className="mb-0.5 block text-[8px] font-bold text-[var(--council-active)] uppercase tracking-widest opacity-70">
                Visual
              </span>
              <p className="line-clamp-2 text-[10px] leading-tight text-[var(--text-muted)] italic opacity-60">
                {(scene as any).visual_prompt || scene.narration || 'Dynamic generation...'}
              </p>
            </div>
          </div>
        </div>
      ))}
    </motion.div>
  );
}
