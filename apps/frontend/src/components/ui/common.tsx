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
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
            <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm" 
                onClick={onClose} 
            />
            <div className="bg-neutral-900 border border-neutral-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col relative z-10 overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-neutral-800">
                    <h2 className="text-lg font-bold text-white">{title}</h2>
                    <button 
                        onClick={onClose}
                        className="p-1 hover:bg-neutral-800 rounded-md text-neutral-400 hover:text-white transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <div className="p-6 overflow-y-auto custom-scrollbar flex-1">
                    {children}
                </div>
            </div>
        </div>
    );
}
