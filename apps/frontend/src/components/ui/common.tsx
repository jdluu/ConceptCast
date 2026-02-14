import { ReactNode } from 'react';

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
    return (
        <div className={`bg-neutral-900 border border-neutral-800 rounded-lg p-6 ${className}`}>
            {children}
        </div>
    );
}

export function Button({
    children,
    onClick,
    disabled = false,
    className = "",
    type = "button",
    title,
}: {
    children: ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    className?: string;
    type?: "button" | "submit" | "reset";
    title?: string;
}) {
    return (
        <button
            type={type}
            onClick={onClick}
            disabled={disabled}
            title={title}
            className={`
                px-4 py-2 rounded-md font-medium transition-colors
                bg-indigo-600 hover:bg-indigo-700 text-white
                disabled:opacity-50 disabled:cursor-not-allowed
                ${className}
            `}
        >
            {children}
        </button>
    );
}
