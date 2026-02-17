import { create } from 'zustand';
import { JobStatus, JobRequest, createJob as apiCreateJob } from '@/lib/api/client';

/**
 * State and actions for managing a ConceptCast generation job.
 */
interface JobState {
    /** The current state and artifacts of the active generation job. */
    currentJob: JobStatus | null;
    /** The original topic submitted by the user. */
    submittedTopic: string;
    /** UNIX timestamp of when the generation was initiated. */
    jobStartedAt: number;
    /** Percentage progress of the video rendering phase (0-100). */
    renderProgress: number;
    /** Whether a create job request is currently in flight. */
    isSubmitting: boolean;
    
    // Actions
    /** Explicitly set the active job data. */
    setCurrentJob: (job: JobStatus | null) => void;
    /** Cache the submitted topic for UI persistence. */
    setSubmittedTopic: (topic: string) => void;
    /** Store the start time for duration tracking. */
    setJobStartedAt: (timestamp: number) => void;
    /** Update rendering percentage, supports functional updates. */
    setRenderProgress: (progress: number | ((prev: number) => number)) => void;
    /** Toggle the global loading state for job creation. */
    setIsSubmitting: (loading: boolean) => void;
    
    /**
     * Reaches out to the backend API to initiate a new generation job.
     * Updates local state with the initial job record and start time.
     *
     * @param {JobRequest} data - Configuration for the new job.
     * @throws {Error} If the API request fails.
     */
    createJob: (data: JobRequest) => Promise<void>;
    /** Resets the job-specific state to initial values. */
    resetJob: () => void;
}

/**
 * Persisted store for managing the lifecycle of ConceptCast jobs.
 * 
 * This store coordinates between the form submission, live SSE updates,
 * and the orchestration view. It tracks the current job's state,
 * rendering progress, and submission status.
 */
export const useJobStore = create<JobState>((set) => ({
    currentJob: null,
    submittedTopic: '',
    jobStartedAt: 0,
    renderProgress: 0,
    isSubmitting: false,

    setCurrentJob: (job) => set({ currentJob: job }),
    setSubmittedTopic: (topic) => set({ submittedTopic: topic }),
    setJobStartedAt: (timestamp) => set({ jobStartedAt: timestamp }),
    setRenderProgress: (progress) => set((state) => ({ 
        renderProgress: typeof progress === 'function' ? progress(state.renderProgress) : progress 
    })),
    setIsSubmitting: (loading) => set({ isSubmitting: loading }),

    createJob: async (data) => {
        set({ isSubmitting: true });
        try {
            const job = await apiCreateJob(data);
            set({ 
                currentJob: job, 
                submittedTopic: data.topic, 
                jobStartedAt: Date.now() 
            });
        } catch (error) {
            console.error('Failed to initiate job:', error);
            throw error;
        } finally {
            set({ isSubmitting: false });
        }
    },

    resetJob: () => set({
        currentJob: null,
        submittedTopic: '',
        jobStartedAt: 0,
        renderProgress: 0,
    }),
}));
