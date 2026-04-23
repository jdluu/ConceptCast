import { LazyMotion, domAnimation } from 'motion/react';
import * as m from 'motion/react-m';

interface RenderingMonitorProps {
  renderProgress: number;
  previewUrl?: string | null;
}

/**
 * Displays a circular progress ring and status text during the Manim rendering phase.
 */
export function RenderingMonitor({ renderProgress, previewUrl }: RenderingMonitorProps) {
  return (
    <section className="animate-in fade-in zoom-in-95 duration-700">
      <div className="border-council-active/20 bg-surface relative overflow-hidden rounded-3xl border p-12 shadow-2xl backdrop-blur-sm">
        {previewUrl && (
          <div className="absolute inset-0 opacity-10">
            <img
              src={previewUrl}
              alt="Preview"
              className="h-full w-full object-cover blur-sm"
            />
          </div>
        )}
        <div className="relative z-10 mx-auto flex max-w-md flex-col items-center text-center">
          <div className="relative mb-10 h-48 w-48">
            {previewUrl && (
              <div className="absolute inset-4 overflow-hidden rounded-full opacity-40">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="h-full w-full object-cover"
                />
              </div>
            )}
            <svg className="h-full w-full -rotate-90 transform" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-surface-border"
              />
              <LazyMotion features={domAnimation}>
                <m.circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeDasharray="283"
                  animate={{ strokeDashoffset: 283 - (283 * (renderProgress || 0)) / 100 }}
                  className="text-council-active"
                />
              </LazyMotion>
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-foreground font-mono text-5xl font-bold tracking-tighter">
                {Math.round(renderProgress || 0)}%
              </span>
              <span className="text-micro text-text-muted font-bold tracking-[0.2em] uppercase">
                Frames rendered
              </span>
            </div>
          </div>
          <h2 className="text-foreground mb-3 text-2xl font-bold tracking-tight">
            Rendering video
          </h2>
          <p className="text-text-muted text-sm leading-relaxed">
            The Animator is executing Manim code to generate high-fidelity educational assets at 60
            frames per second.
          </p>
        </div>
      </div>
    </section>
  );
}
