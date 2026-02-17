/**
 * Formats a duration in seconds into a digital timestamp format (e.g., 0:45, 1:20:15).
 */
export function formatDuration(seconds: number | undefined | null): string {
    if (seconds === undefined || seconds === null) return '0:00';
    
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    
    if (h > 0) {
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }
    return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * Formats a duration in seconds into a human-readable descriptive format (e.g., 2m 15s).
 */
export function formatGenerationTime(seconds: number | undefined | null): string {
    if (seconds === undefined || seconds === null) return '0s';
    
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    
    if (m > 0) {
        return `${m}m ${s}s`;
    }
    return `${s}s`;
}
