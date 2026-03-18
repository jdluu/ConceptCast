import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

/**
 * Base card for artifact items (Scenes, Teaching Steps).
 */
export function ArtifactCard({
  children,
  className,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={cn(
        'border-surface-border bg-background hover:border-council-active/30 flex flex-col rounded-xl border p-3 shadow-sm transition-all',
        className,
      )}
    >
      {children}
    </motion.div>
  );
}

/**
 * Empty or Loading state for artifact sections.
 */
export function ArtifactPlaceholder({
  status = 'loading',
  message,
  submessage,
}: {
  status?: 'queued' | 'loading';
  message?: string;
  submessage?: string;
}) {
  const isQueued = status === 'queued';

  return (
    <div
      className={cn(
        'border-surface-border bg-surface/30 text-text-muted flex h-40 flex-col items-center justify-center space-y-4 rounded-2xl border p-8 transition-all duration-700',
        isQueued ? 'border-dashed opacity-30 grayscale' : 'animate-pulse',
      )}
    >
      {!isQueued ? (
        <div className="relative">
          <div className="bg-council-active/20 absolute inset-0 animate-pulse rounded-full blur-lg" />
          <div className="border-surface-border border-t-council-active shadow-glow-council relative h-10 w-10 animate-spin rounded-full border-2" />
        </div>
      ) : (
        <div className="border-surface-border flex h-10 w-10 items-center justify-center rounded-full border-2 border-dashed">
          <div className="bg-surface-border h-4 w-4 rounded-full opacity-50" />
        </div>
      )}
      <div className="space-y-1 text-center">
        <p className="text-foreground/60 text-[10px] font-bold tracking-[0.2em] uppercase">
          {message || (isQueued ? 'Pipeline Queued' : 'Agent Deliberation')}
        </p>
        <p className="text-[9px] font-medium italic opacity-50">
          {submessage ||
            (isQueued
              ? 'Awaiting council authorization...'
              : 'Synthesizing knowledge structures...')}
        </p>
      </div>
    </div>
  );
}

/**
 * Small labeled badge for artifact metadata.
 */
export function ArtifactBadge({
  children,
  variant = 'default',
}: {
  children: ReactNode;
  variant?: 'default' | 'active' | 'completed';
}) {
  const variants = {
    default: 'text-text-muted',
    active: 'text-council-active',
    completed: 'text-council-completed',
  };

  return (
    <span
      className={cn(
        'text-nano mb-0.5 block font-bold tracking-widest uppercase opacity-70',
        variants[variant],
      )}
    >
      {children}
    </span>
  );
}

/**
 * Standard action button for artifact views.
 */
export function ArtifactAction({
  onClick,
  children,
}: {
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className="text-micro text-text-muted hover:text-council-active w-full py-2 font-bold tracking-[0.2em] uppercase transition-colors"
    >
      {children}
    </button>
  );
}
