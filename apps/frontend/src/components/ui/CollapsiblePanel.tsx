import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { Card } from '@/components/ui/Card';

interface CollapsiblePanelProps {
  /** Header title text. */
  title: string;
  /** Optional lucide icon component rendered beside the title. */
  icon?: any;
  /** Panel body content. */
  children: React.ReactNode;
  /** Whether the panel starts expanded. Defaults to true. */
  defaultOpen?: boolean;
}

/**
 * An animated disclosure panel with a Card wrapper.
 *
 * @param {CollapsiblePanelProps} props - Component properties.
 * @returns {JSX.Element} The rendered collapsible panel.
 */
export function CollapsiblePanel({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
}: CollapsiblePanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Card className="overflow-hidden border-[var(--surface-border)] bg-[var(--surface)] shadow-sm transition-all duration-300">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="group flex w-full items-center justify-between px-6 py-4 text-left transition-colors hover:bg-[var(--background)]/50"
        aria-expanded={open}
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className="h-4 w-4 text-indigo-500" />}
          <span className="text-xs font-bold tracking-wider text-[var(--foreground)] uppercase">
            {title}
          </span>
        </div>
        <ChevronDown
          className={`h-4 w-4 text-[var(--text-muted)] transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <div className="px-6 pt-0 pb-6">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
