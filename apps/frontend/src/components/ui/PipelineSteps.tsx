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
        return STEPS.findIndex(s => s.id === status);
    }, [status]);

    return (
        <div className="w-full pt-6 pb-14">
            <div className="relative flex items-center justify-between w-full">
                {/* Background Line */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-[var(--surface-border)] rounded-full -z-10" />
                
                {/* Active Line (Progress) */}
                <motion.div 
                    initial={{ width: 0 }}
                    animate={{ 
                        width: `${Math.min(100, (Math.max(0, currentStepIndex) / (STEPS.length - 1)) * 100)}%` 
                    }}
                    transition={{ type: 'spring', stiffness: 50, damping: 20 }}
                    className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-indigo-500 rounded-full -z-10"
                />

                {STEPS.map((step, index) => {
                    const isCompleted = currentStepIndex > index || status === 'completed';
                    const isCurrent = currentStepIndex === index;
                    const isPending = currentStepIndex < index && status !== 'completed';

                    return (
                        <div key={step.id} className="flex flex-col items-center relative flex-1 min-w-0">
                            {/* Step Circle */}
                            <motion.div 
                                layout
                                animate={{
                                    scale: isCurrent ? 1.15 : 1,
                                    backgroundColor: isCompleted ? '#6366f1' : 'var(--background)',
                                    borderColor: (isCompleted || isCurrent) ? '#6366f1' : 'var(--surface-border)',
                                    boxShadow: isCurrent ? '0 0 20px rgba(99,102,241,0.4)' : 'none'
                                }}
                                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors z-10 shrink-0
                                    ${isCompleted ? 'text-white' : ''}
                                    ${isCurrent ? 'text-indigo-500' : ''}
                                    ${isPending ? 'text-[var(--text-muted)]' : ''}
                                `}
                            >
                                <AnimatePresence mode="wait">
                                    {isCompleted ? (
                                        <motion.svg 
                                            key="check"
                                            initial={{ opacity: 0, scale: 0.5 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            className="w-4 h-4" 
                                            fill="none" 
                                            viewBox="0 0 24 24" 
                                            stroke="currentColor"
                                        >
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
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
                            <div className="absolute top-10 w-full flex flex-col items-center">
                                <motion.span 
                                    animate={{ 
                                        color: isCurrent ? 'var(--foreground)' : (isCompleted ? 'var(--text-muted)' : 'var(--text-muted)'),
                                        opacity: isCurrent ? 1 : 0.6 
                                    }}
                                    className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider mb-0.5 whitespace-nowrap px-1"
                                >
                                    {isCurrent ? step.label : (window.innerWidth > 640 ? step.label : (index + 1))}
                                </motion.span>
                                <AnimatePresence>
                                    {isCurrent && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 5 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -5 }}
                                            className="text-[9px] sm:text-[10px] text-indigo-300 italic text-center w-max max-w-[120px] px-2 leading-tight"
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
