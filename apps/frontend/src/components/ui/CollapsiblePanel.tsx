import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import * as m from 'motion/react-m';
import { ChevronDown } from 'lucide-react';
import { Card } from '@/components/ui/Card';

interface CollapsiblePanelProps {
  /** Header title text. */
  title: string;
  /** Optional lucide icon component rendered beside the title. */
  icon?: any;
  /** Panel body content. */
  children: React.ReactNode;
  /** Controlled open state (optional). */
  open?: boolean;
  /** Controlled state setter (optional). */
  onOpenChange?: (open: boolean) => void;
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
  open,
  onOpenChange,
}: CollapsiblePanelProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = useState(true);
  const isOpen = open ?? uncontrolledOpen;
  const setOpen = onOpenChange ?? setUncontrolledOpen;

  return (
    <Card className="border-surface-border bg-surface overflow-hidden shadow-sm transition-all duration-300">
      <button
        type="button"
        onClick={() => setOpen(!isOpen)}
        className="group hover:bg-background/50 flex w-full items-center justify-between px-6 py-4 text-left transition-colors"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className="text-council-active h-4 w-4" />}
          <span className="text-foreground text-xs font-bold tracking-wider uppercase">
            {title}
          </span>
        </div>
        <ChevronDown
          className={`text-text-muted h-4 w-4 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
          aria-hidden
        />
      </button>
      <AnimatePresence>
        {isOpen && (
          <m.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
          >
            <div className="px-6 pt-0 pb-6">{children}</div>
          </m.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
