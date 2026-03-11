import { ReactNode } from 'react';
import { Button as BaseButton } from '@/components/ui/Button';
import { Card as BaseCard } from '@/components/ui/Card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';

/**
 * Premium Card component for ConceptCast surfaces.
 * Now a thin wrapper around the base Card with 'premium' variant.
 */
export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <BaseCard variant="premium" className={className}>
      {children}
    </BaseCard>
  );
}

/**
 * Premium Button component for ConceptCast actions.
 * Now a thin wrapper around the base Button with 'premium' variant.
 */
export function Button({
  children,
  onClick,
  disabled = false,
  className = '',
  type = 'button',
  title,
  variant = 'primary',
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
  title?: string;
  variant?: 'primary' | 'outline';
}) {
  return (
    <BaseButton
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      variant={variant === 'primary' ? 'premium' : 'outline'}
      size={variant === 'primary' ? 'xl' : 'default'}
      rounded="xl"
      className={className}
    >
      {children}
    </BaseButton>
  );
}

/**
 * Centered modal dialog with standard ConceptCast styling.
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
      <DialogContent className="flex max-h-[90vh] max-w-2xl flex-col overflow-hidden border-surface-border bg-surface p-0">
        <DialogHeader className="border-b border-surface-border p-4">
          <DialogTitle className="text-lg font-bold text-foreground">{title}</DialogTitle>
          <DialogDescription className="sr-only">Modal dialog for {title}</DialogDescription>
        </DialogHeader>
        <div className="custom-scrollbar flex-1 overflow-y-auto p-6">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
