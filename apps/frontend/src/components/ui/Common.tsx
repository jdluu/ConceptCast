import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Button as ShadcnButton } from '@/components/ui/Button';
import { Card as ShadcnCard } from '@/components/ui/Card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <ShadcnCard
      className={cn(
        'relative overflow-hidden rounded-2xl border-[var(--surface-border)] bg-[var(--surface)]/50 p-6 shadow-2xl backdrop-blur-xl',
        'before:pointer-events-none before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/5 before:to-transparent',
        className,
      )}
    >
      {children}
    </ShadcnCard>
  );
}

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
    <ShadcnButton
      type={type}
      onClick={onClick}
      disabled={disabled}
      title={title}
      variant={variant === 'primary' ? 'default' : 'outline'}
      className={cn(
        'rounded-xl font-extrabold transition-all duration-300 active:scale-[0.97]',
        variant === 'primary' && [
          'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500',
          'border-none text-white shadow-xl shadow-indigo-500/25',
          'hover:-translate-y-0.5 hover:shadow-indigo-500/40',
        ],
        variant === 'outline' && 'border-2 hover:bg-[var(--surface)]',
        className,
      )}
    >
      {children}
    </ShadcnButton>
  );
}

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
      <DialogContent className="flex max-h-[90vh] max-w-2xl flex-col overflow-hidden border-[var(--surface-border)] bg-[var(--surface)] p-0">
        <DialogHeader className="border-b border-[var(--surface-border)] p-4">
          <DialogTitle className="text-lg font-bold text-[var(--foreground)]">{title}</DialogTitle>
          <DialogDescription className="sr-only">Modal dialog for {title}</DialogDescription>
        </DialogHeader>
        <div className="custom-scrollbar flex-1 overflow-y-auto p-6">{children}</div>
      </DialogContent>
    </Dialog>
  );
}
