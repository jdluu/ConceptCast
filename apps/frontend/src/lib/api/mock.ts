import { type JobSummary, type JobStatus } from '@/lib/api/types';

export const MOCK_JOBS_SUMMARY: JobSummary[] = [
    {
        job_id: 'mock-job-completed-1',
        topic: 'The Quantum World: Entanglement Explained',
        status: 'completed',
        mode: 'mock',
        created_at: new Date(Date.now() - 3600000 * 2).toISOString(), // 2 hours ago
        duration_seconds: 145,
        cost: 0.12,
        thumbnail_url: 'https://placehold.co/600x400/1e1e1e/4f46e5?text=Quantum+Entanglement',
        video_metadata: {
            resolution: '1920x1080',
            duration: 145,
            bitrate: '5.2Mbps',
            file_size: '24MB',
            format: 'mp4'
        }
    } as any,
    {
        job_id: 'mock-job-active-1',
        topic: 'Photosynthesis: The Engine of Life',
        status: 'rendering',
        mode: 'mock',
        created_at: new Date(Date.now() - 600000).toISOString(), // 10 mins ago
        duration_seconds: null,
        cost: 0.05,
    } as any,
    {
        job_id: 'mock-job-failed-1',
        topic: 'Advanced Calculus: Taylor Series',
        status: 'failed',
        mode: 'mock',
        created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        duration_seconds: 45,
        cost: 0.02,
    } as any
];

export const MOCK_JOB_DETAILS: Record<string, JobStatus> = {
    'mock-job-completed-1': {
        job_id: 'mock-job-completed-1',
        topic: 'The Quantum World: Entanglement Explained',
        status: 'completed',
        mode: 'mock',
        created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        started_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        finished_at: new Date(Date.now() - 3600000 * 2 + 145000).toISOString(),
        duration_seconds: 145,
        target_audience: 'University Student',
        manim_code: `from manim import *

class QuantumEntanglement(Scene):
    def construct(self):
        # Create two entangled particles
        p1 = Dot(color=BLUE).shift(LEFT * 2)
        p2 = Dot(color=BLUE).shift(RIGHT * 2)
        
        self.play(FadeIn(p1), FadeIn(p2))
        self.play(Indicate(p1), Indicate(p2))
        
        # Show entanglement link
        link = Line(p1.get_center(), p2.get_center(), color=YELLOW)
        self.play(Create(link))
        self.wait()`,
        video_url: 'https://www.w3schools.com/html/mov_bbb.mp4', // Example video
        cost: 0.12,
        thumbnail_url: 'https://placehold.co/600x400/1e1e1e/4f46e5?text=Quantum+Entanglement',
        video_metadata: {
            resolution: '1920x1080',
            duration: 145,
            bitrate: '5.2Mbps',
            file_size: '24MB',
            format: 'mp4'
        },
        streamed_thoughts: [
            { agent: 'analyst', phase: 'research', content: 'Analyzing quantum entanglement principles and non-locality.' },
            { agent: 'architect', phase: 'storyboarding', content: 'Designing a visual representation of Bell states.' },
            { agent: 'animator', phase: 'coding', content: 'Generating Manim code for particle interaction.' }
        ]
    } as any,
    'mock-job-active-1': {
        job_id: 'mock-job-active-1',
        topic: 'Photosynthesis: The Engine of Life',
        status: 'rendering',
        mode: 'mock',
        created_at: new Date(Date.now() - 600000).toISOString(),
        target_audience: 'High School Student',
        streamed_thoughts: [
            { agent: 'analyst', phase: 'research', content: 'Extracting key components of the Calvin cycle.' },
            { agent: 'architect', phase: 'storyboarding', content: 'Visualizing photon absorption in chlorophyll.' }
        ]
    } as any,
    'mock-job-failed-1': {
        job_id: 'mock-job-failed-1',
        topic: 'Advanced Calculus: Taylor Series',
        status: 'failed',
        mode: 'mock',
        error: 'AnimationGenerationError: Manim failed to render scene. Syntax error in generated code at line 42.',
        created_at: new Date(Date.now() - 7200000).toISOString(),
        target_audience: 'Expert',
    } as any
};
