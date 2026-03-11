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
      "flex h-32 flex-col items-center justify-center space-y-3 py-12 text-text-muted",
      isQueued && "rounded-xl border border-dashed border-surface-border opacity-40"
    )}>
      {!isQueued && (
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-surface-border border-t-council-active shadow-sm" />
      )}
      <div className="text-center">
        <p className="text-tiny font-bold tracking-widest uppercase">
          {message || (isQueued ? 'Queued' : 'Processing')}
        </p>
        <p className="text-micro italic opacity-60">
          {submessage || (isQueued ? 'Awaiting prior stage completion...' : 'Deliberating...')}
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
