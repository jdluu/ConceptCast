import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface CollapsibleSectionProps {
  title: string;
  isCollapsed: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  icon?: React.ReactNode;
  badge?: React.ReactNode;
}

export function CollapsibleSection({
  title,
  isCollapsed,
  onToggle,
  children,
  icon,
  badge,
}: CollapsibleSectionProps) {
  return (
    <div className="border-surface-border bg-surface overflow-hidden rounded-2xl border shadow-lg transition-all duration-300">
      <button
        onClick={onToggle}
        className="border-surface-border bg-surface/50 hover:bg-surface-border/20 flex w-full items-center justify-between border-b px-4 py-3 transition-colors"
      >
        <div className="flex items-center gap-3">
          {icon && (
            <motion.span
              animate={{ opacity: isCollapsed ? 0.4 : [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="flex h-2 w-2 items-center justify-center"
            >
              {icon}
            </motion.span>
          )}
          <span className="text-mini text-foreground font-bold tracking-widest uppercase">
            {title}
          </span>
          {badge && <div className="ml-2">{badge}</div>}
        </div>
        <div className="flex items-center gap-3">
          {isCollapsed ? (
            <ChevronDown className="text-text-muted h-3.5 w-3.5" />
          ) : (
            <ChevronUp className="text-text-muted h-3.5 w-3.5" />
          )}
        </div>
      </button>

      <AnimatePresence initial={false}>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <div className="p-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
