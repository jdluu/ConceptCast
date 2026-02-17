import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Button as ShadcnButton } from '@/components/ui/Button';
import { Card as ShadcnCard } from '@/components/ui/Card';
import { 
    Dialog, 
    DialogContent, 
    DialogHeader, 
    DialogTitle,
    DialogDescription
} from '@/components/ui/Dialog';

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
    return (
        <ShadcnCard className={cn(
            "rounded-2xl p-6 border-[var(--surface-border)] bg-[var(--surface)]/50 backdrop-blur-xl shadow-2xl relative overflow-hidden",
            "before:absolute before:inset-0 before:bg-gradient-to-br before:from-white/5 before:to-transparent before:pointer-events-none",
            className
        )}>
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
                "rounded-xl font-extrabold transition-all duration-300 active:scale-[0.97]",
                variant === "primary" && [
                    "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500",
                    "shadow-xl shadow-indigo-500/25 border-none text-white",
                    "hover:shadow-indigo-500/40 hover:-translate-y-0.5"
                ],
                variant === "outline" && "border-2 hover:bg-[var(--surface)]",
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
