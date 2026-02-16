import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VideoPlayerProps {
    src: string | null;
    poster?: string;
    autoPlay?: boolean;
    loop?: boolean;
    className?: string;
    description?: string;
}

export function VideoPlayer({ 
    src, 
    poster, 
    autoPlay = true, 
    loop = true, 
    className,
    description
}: VideoPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Reset state when src changes
    useEffect(() => {
        setIsLoading(true);
        setError(null);
        if (videoRef.current) {
            videoRef.current.load();
        }
    }, [src]);

    const handleCanPlay = () => {
        setIsLoading(false);
        if (autoPlay && videoRef.current) {
            videoRef.current.play().catch(e => {
                console.warn("Autoplay prevented:", e);
            });
        }
    };

    const handleError = () => {
        setIsLoading(false);
        setError("Unable to load video stream. The file might still be processing.");
    };

    const handleRetry = () => {
        if (videoRef.current && src) {
            setError(null);
            setIsLoading(true);
            // Append timestamp to force cache bypass if referencing a freshly generated file
            const separator = src.includes('?') ? '&' : '?';
            videoRef.current.src = `${src}${separator}t=${Date.now()}`;
            videoRef.current.load();
        }
    };

    return (
        <div className={cn("relative group overflow-hidden rounded-xl bg-[var(--background)] border border-[var(--surface-border)] shadow-2xl", className)}>
            {/* Main Video Element */}
            {src ? (
                <video
                    ref={videoRef}
                    className={cn("w-full h-full object-contain transition-opacity duration-700", 
                        isLoading ? "opacity-0" : "opacity-100"
                    )}
                    playsInline
                    loop={loop}
                    muted={autoPlay} // Muted required for autoplay policy
                    controls
                    poster={poster}
                    onCanPlay={handleCanPlay}
                    onError={handleError}
                >
                    <source src={src} type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-[var(--surface)]/50">
                    <p className="text-[var(--text-muted)] text-sm font-medium">No video source available</p>
                </div>
            )}

            {/* Overlay: Loading State */}
            <AnimatePresence>
                {isLoading && src && !error && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--surface)]/80 backdrop-blur-sm z-10"
                    >
                        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-3" />
                        <p className="text-[var(--text-muted)] text-xs font-medium uppercase tracking-widest animate-pulse">
                            Loading Stream...
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Overlay: Error State */}
            <AnimatePresence>
                {error && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 flex flex-col items-center justify-center bg-[var(--surface)]/95 z-20 p-6 text-center"
                    >
                        <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4 border border-red-500/20">
                            <AlertCircle className="w-6 h-6 text-red-500" />
                        </div>
                        <h3 className="text-[var(--foreground)] font-bold mb-2 uppercase tracking-tight">Stream Error</h3>
                        <p className="text-[var(--text-muted)] text-sm mb-6 max-w-xs">{error}</p>
                        <button 
                            onClick={handleRetry}
                            className="flex items-center gap-2 px-4 py-2 bg-[var(--surface)] hover:bg-[var(--surface-border)] text-[var(--foreground)] rounded-lg transition-colors text-sm font-bold border border-[var(--surface-border)]"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Retry Connection
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Overlay: Description / Caption */}
            {description && !isLoading && !error && (
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-[var(--background)] via-[var(--background)]/40 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <p className="text-[var(--foreground)] font-bold text-shadow-sm">{description}</p>
                </div>
            )}
        </div>
    );
}
