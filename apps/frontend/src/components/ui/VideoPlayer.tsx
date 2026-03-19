import { useState, useRef, useEffect } from 'react';
import { AnimatePresence } from 'motion/react';
import * as m from 'motion/react-m';
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
        'group border-surface-border bg-background relative overflow-hidden rounded-xl border shadow-2xl',
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
        <div className="bg-surface/50 absolute inset-0 flex items-center justify-center">
          <p className="text-text-muted text-sm font-medium">No video source available</p>
        </div>
      )}

      {/* Overlay: Loading State */}
      <AnimatePresence>
        {isLoading && src && !error && (
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-surface/80 absolute inset-0 z-10 flex flex-col items-center justify-center backdrop-blur-sm"
          >
            <Loader2 className="text-council-active mb-3 h-10 w-10 animate-spin" />
            <p className="text-tiny text-text-muted animate-pulse font-bold tracking-[0.2em] uppercase">
              Loading Stream...
            </p>
          </m.div>
        )}
      </AnimatePresence>

      {/* Overlay: Error State */}
      <AnimatePresence>
        {error && (
          <m.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-surface/95 absolute inset-0 z-20 flex flex-col items-center justify-center p-6 text-center"
          >
            <div className="border-destructive/20 bg-destructive/10 mb-4 flex h-12 w-12 items-center justify-center rounded-full border">
              <AlertCircle className="text-destructive h-6 w-6" />
            </div>
            <h3 className="text-foreground mb-2 font-bold tracking-tight uppercase">
              Stream Error
            </h3>
            <p className="text-text-muted mb-6 max-w-xs text-sm">{error}</p>
            <button
              onClick={handleRetry}
              className="border-surface-border bg-surface text-foreground hover:bg-surface-border flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-bold transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Retry Connection
            </button>
          </m.div>
        )}
      </AnimatePresence>

      {/* Overlay: Description / Caption */}
      {description && !isLoading && !error && (
        <div className="from-background via-background/40 pointer-events-none absolute right-0 bottom-0 left-0 bg-gradient-to-t to-transparent p-6 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <p className="text-foreground font-bold text-shadow-sm">{description}</p>
        </div>
      )}
    </div>
  );
}
