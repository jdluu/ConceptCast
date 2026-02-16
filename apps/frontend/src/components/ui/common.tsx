import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Button as ShadcnButton } from './button';
import { Card as ShadcnCard } from './card';
import { 
    Dialog, 
    DialogContent, 
    DialogHeader, 
    DialogTitle,
    DialogDescription
} from './dialog';

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
    return (
        <ShadcnCard className={cn("rounded-xl p-6", className)}>
            {children}
        </ShadcnCard>
    );
}

export function Button({
    children,
    onClick,
    disabled = false,
    className = "",
    type = "button",
    title,
    variant = "primary",
}: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    className?: string;
    type?: "button" | "submit" | "reset";
    title?: string;
    variant?: "primary" | "outline";
}) {
    return (
        <ShadcnButton
            type={type}
            onClick={onClick}
            disabled={disabled}
            title={title}
            variant={variant === "primary" ? "default" : "outline"}
            className={cn(
                "rounded-xl font-bold active:scale-[0.98]",
                variant === "primary" && "shadow-lg shadow-indigo-500/20",
                className
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
    children 
}: { 
    isOpen: boolean; 
    onClose: () => void; 
    title: string; 
    children: ReactNode; 
}) {
    return (
        <Dialog open={isOpen} onOpenChange={(open: boolean) => !open && onClose()}>
            <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col p-0 overflow-hidden border-[var(--surface-border)] bg-[var(--surface)]">
                <DialogHeader className="p-4 border-b border-[var(--surface-border)]">
                    <DialogTitle className="text-lg font-bold text-[var(--foreground)]">{title}</DialogTitle>
                    <DialogDescription className="sr-only">
                        Modal dialog for {title}
                    </DialogDescription>
                </DialogHeader>
                <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
                    {children}
                </div>
            </DialogContent>
        </Dialog>
    );
}
