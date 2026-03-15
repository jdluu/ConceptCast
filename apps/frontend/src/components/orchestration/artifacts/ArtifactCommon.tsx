import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

/**
 * Base card for artifact items (Scenes, Teaching Steps).
 */
export function ArtifactCard({ 
  children, 
  className,
  delay = 0 
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
        "flex flex-col rounded-xl border border-surface-border bg-background p-3 shadow-sm transition-all hover:border-council-active/30",
        className
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
  submessage
}: {
  status?: 'queued' | 'loading';
  message?: string;
  submessage?: string;
}) {
  const isQueued = status === 'queued';
  
  return (
    <div className={cn(
      "flex h-40 flex-col items-center justify-center space-y-4 rounded-2xl border border-surface-border bg-surface/30 p-8 text-text-muted transition-all duration-700",
      isQueued ? "border-dashed opacity-30 grayscale" : "animate-pulse"
    )}>
      {!isQueued ? (
        <div className="relative">
          <div className="absolute inset-0 blur-lg bg-council-active/20 rounded-full animate-pulse" />
          <div className="relative h-10 w-10 rounded-full border-2 border-surface-border border-t-council-active shadow-glow-council animate-spin" />
        </div>
      ) : (
        <div className="h-10 w-10 rounded-full border-2 border-dashed border-surface-border flex items-center justify-center">
          <div className="h-4 w-4 rounded-full bg-surface-border opacity-50" />
        </div>
      )}
      <div className="text-center space-y-1">
        <p className="text-[10px] font-bold tracking-[0.2em] uppercase text-foreground/60">
          {message || (isQueued ? 'Pipeline Queued' : 'Agent Deliberation')}
        </p>
        <p className="text-[9px] font-medium italic opacity-50">
          {submessage || (isQueued ? 'Awaiting council authorization...' : 'Synthesizing knowledge structures...')}
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
  variant = 'default' 
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
    <span className={cn(
      "mb-0.5 block text-nano font-bold uppercase tracking-widest opacity-70",
      variants[variant]
    )}>
      {children}
    </span>
  );
}

/**
 * Standard action button for artifact views.
 */
export function ArtifactAction({ 
  onClick, 
  children 
}: { 
  onClick: () => void; 
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full py-2 text-micro font-bold tracking-[0.2em] text-text-muted uppercase transition-colors hover:text-council-active"
    >
      {children}
    </button>
  );
}
