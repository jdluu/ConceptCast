import { motion, AnimatePresence } from 'framer-motion';

/**
 * A full-screen loading state displayed while the job is being submitted.
 */
export const LoadingOverlay = ({ isLoading }: { isLoading: boolean }) => (
  <AnimatePresence>
    {isLoading && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-surface/90 backdrop-blur-md"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="h-12 w-12 rounded-full border-4 border-council-active border-t-transparent shadow-lg shadow-council-active/10"
        />
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-tiny font-bold tracking-[0.2em] text-foreground uppercase"
          aria-live="polite"
        >
          Summoning the Council...
        </motion.p>
      </motion.div>
    )}
  </AnimatePresence>
);

/**
 * Warning banner shown when no persistent AI provider keys are detected.
 */
export const NoKeysAlert = ({
  developerMode,
  onClose,
}: {
  developerMode: boolean;
  onClose: () => void;
}) => (
  <motion.div
    initial={{ opacity: 0, height: 0 }}
    animate={{ opacity: 1, height: 'auto' }}
    className="mb-8 flex items-start justify-between gap-4 rounded-xl border border-warning/20 bg-warning/10 p-4 text-sm text-warning-foreground dark:text-warning"
    role="alert"
  >
    <span>
      {developerMode
        ? 'No API keys configured. Add keys to generate lessons, or run a mock demo below.'
        : 'No API keys configured. Add keys in your environment, or enable Developer mode in Settings to run a mock demo.'}
    </span>
    <button
      type="button"
      onClick={onClose}
      className="shrink-0 rounded p-0.5 text-warning/60 transition-colors hover:text-warning"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-4 w-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </motion.div>
);
