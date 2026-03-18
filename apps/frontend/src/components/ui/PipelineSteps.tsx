import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { JobStatus } from '@/lib/api/types';

interface PipelineStepsProps {
  status: JobStatus['status'];
}

const STEPS = [
  { id: 'planning', label: 'Planning', description: 'Analyst creating curriculum' },
  { id: 'validating', label: 'Validating', description: 'Validator checking accuracy' },
  { id: 'architecting', label: 'Architecting', description: 'Architect designing scenes' },
  { id: 'animating', label: 'Animating', description: 'Generating Manim code' },
  { id: 'rendering', label: 'Rendering', description: 'Animator generating video' },
  { id: 'reviewing', label: 'Reviewing', description: 'Reviewing quality' },
];

export function PipelineSteps({ status }: PipelineStepsProps) {
  const currentStepIndex = useMemo(() => {
    if (status === 'completed') return STEPS.length;
    if (status === 'failed') return -1;
    return STEPS.findIndex((s) => s.id === status);
  }, [status]);

  return (
    <div className="w-full pt-6 pb-14">
      <div className="relative flex w-full items-center justify-between">
        {/* Background Line */}
        <div className="bg-surface-border absolute top-1/2 left-0 -z-10 h-1 w-full -translate-y-1/2 rounded-full" />

        {/* Active Line (Progress) */}
        <motion.div
          initial={{ width: 0 }}
          animate={{
            width: `${Math.min(100, (Math.max(0, currentStepIndex) / (STEPS.length - 1)) * 100)}%`,
          }}
          transition={{ type: 'spring', stiffness: 50, damping: 20 }}
          className="bg-council-active absolute top-1/2 left-0 -z-10 h-1 -translate-y-1/2 rounded-full"
        />

        {STEPS.map((step, index) => {
          const isCompleted = currentStepIndex > index || status === 'completed';
          const isCurrent = currentStepIndex === index;
          const isPending = currentStepIndex < index && status !== 'completed';

          return (
            <div key={step.id} className="relative flex min-w-0 flex-1 flex-col items-center">
              {/* Step Circle */}
              <motion.div
                layout
                animate={{
                  scale: isCurrent ? 1.15 : 1,
                  backgroundColor: isCompleted ? 'var(--council-completed)' : 'var(--background)',
                  borderColor:
                    isCompleted || isCurrent ? 'var(--council-active)' : 'var(--surface-border)',
                  boxShadow: isCurrent ? '0 0 20px rgba(59,130,246,0.4)' : 'none',
                }}
                className={`z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${isCompleted ? 'text-white' : ''} ${isCurrent ? 'text-council-active' : ''} ${isPending ? 'text-text-muted' : ''} `}
              >
                <AnimatePresence mode="wait">
                  {isCompleted ? (
                    <motion.svg
                      key="check"
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={3}
                        d="M5 13l4 4L19 7"
                      />
                    </motion.svg>
                  ) : (
                    <motion.span
                      key="index"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-xs font-bold"
                    >
                      {index + 1}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.div>

              {/* Label */}
              <div className="absolute top-10 flex w-full flex-col items-center">
                <motion.span
                  animate={{
                    color: isCurrent
                      ? 'var(--foreground)'
                      : isCompleted
                        ? 'var(--text-muted)'
                        : 'var(--text-muted)',
                    opacity: isCurrent ? 1 : 0.6,
                  }}
                  className="text-tiny sm:text-mini mb-0.5 px-1 font-bold tracking-wider whitespace-nowrap uppercase"
                >
                  {isCurrent ? step.label : window.innerWidth > 640 ? step.label : index + 1}
                </motion.span>
                <AnimatePresence>
                  {isCurrent && (
                    <motion.div
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -5 }}
                      className="text-micro text-council-active sm:text-tiny w-max max-w-3xs px-2 text-center leading-tight italic"
                    >
                      {step.description}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
