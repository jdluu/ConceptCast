import { cn } from '@/lib/utils';

interface ActionButtonProps {
  /** Icon node rendered inside the button. */
  icon: React.ReactNode;
  /** Tooltip title for the button. */
  title: string;
  /** Click handler. */
  onClick: (e: React.MouseEvent) => void;
  /** Visual variant controlling hover color. */
  variant?: 'default' | 'danger';
}

/**
 * A compact icon-only action button with hover color feedback.
 *
 * @param {ActionButtonProps} props - Component properties.
 * @returns {JSX.Element} The rendered action button.
 */
export function ActionButton({ icon, title, onClick, variant = 'default' }: ActionButtonProps) {
  return (
    <button
      title={title}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onClick(e);
      }}
      className={cn(
        'rounded-lg p-2 shadow-sm transition-all active:scale-95',
        variant === 'danger'
          ? 'text-text-muted hover:bg-destructive/10 hover:text-destructive'
          : 'text-text-muted hover:bg-council-active/10 hover:text-council-active',
      )}
    >
      {icon}
    </button>
  );
}
