import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility to merge tailwind classes with support for conditional logic.
 * Uses clsx and tailwind-merge to resolve conflicts.
 */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/**
 * Formats a duration in seconds to "Xm Ys" format.
 */
export function formatDuration(seconds: number | null | undefined): string {
    if (seconds === null || seconds === undefined) return '-';
    if (seconds < 60) return `${Math.floor(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (secs === 0) return `${mins}m`;
    return `${mins}m ${secs}s`;
}
