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
  description,
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
      videoRef.current.play().catch((e) => {
        console.warn('Autoplay prevented:', e);
      });
    }
  };

  const handleError = () => {
    setIsLoading(false);
    setError('Unable to load video stream. The file might still be processing.');
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
    <div
      className={cn(
        'group relative overflow-hidden rounded-xl border border-[var(--surface-border)] bg-[var(--background)] shadow-2xl',
        className,
      )}
    >
      {/* Main Video Element */}
      {src ? (
        <video
          ref={videoRef}
          className={cn(
            'h-full w-full object-contain transition-opacity duration-700',
            isLoading ? 'opacity-0' : 'opacity-100',
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
          <p className="text-sm font-medium text-[var(--text-muted)]">No video source available</p>
        </div>
      )}

      {/* Overlay: Loading State */}
      <AnimatePresence>
        {isLoading && src && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[var(--surface)]/80 backdrop-blur-sm"
          >
            <Loader2 className="mb-3 h-10 w-10 animate-spin text-indigo-500" />
            <p className="animate-pulse text-xs font-medium tracking-widest text-[var(--text-muted)] uppercase">
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
            className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[var(--surface)]/95 p-6 text-center"
          >
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-red-500/20 bg-red-500/10">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <h3 className="mb-2 font-bold tracking-tight text-[var(--foreground)] uppercase">
              Stream Error
            </h3>
            <p className="mb-6 max-w-xs text-sm text-[var(--text-muted)]">{error}</p>
            <button
              onClick={handleRetry}
              className="flex items-center gap-2 rounded-lg border border-[var(--surface-border)] bg-[var(--surface)] px-4 py-2 text-sm font-bold text-[var(--foreground)] transition-colors hover:bg-[var(--surface-border)]"
            >
              <RefreshCw className="h-4 w-4" />
              Retry Connection
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Overlay: Description / Caption */}
      {description && !isLoading && !error && (
        <div className="pointer-events-none absolute right-0 bottom-0 left-0 bg-gradient-to-t from-[var(--background)] via-[var(--background)]/40 to-transparent p-6 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <p className="font-bold text-[var(--foreground)] text-shadow-sm">{description}</p>
        </div>
      )}
    </div>
  );
}
