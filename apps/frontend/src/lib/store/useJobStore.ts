import { create } from 'zustand';
import { JobStatus, CreateJobRequest, createJob as apiCreateJob } from '../api';

interface JobState {
    currentJob: JobStatus | null;
    submittedTopic: string;
    jobStartedAt: number;
    renderProgress: number;
    isSubmitting: boolean;
    
    // Actions
    setCurrentJob: (job: JobStatus | null) => void;
    setSubmittedTopic: (topic: string) => void;
    setJobStartedAt: (timestamp: number) => void;
    setRenderProgress: (progress: number | ((prev: number) => number)) => void;
    setIsSubmitting: (loading: boolean) => void;
    
    createJob: (data: CreateJobRequest) => Promise<void>;
    resetJob: () => void;
}

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
