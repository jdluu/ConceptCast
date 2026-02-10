import { JobStatus, JobStatusEnum } from '../../lib/api';

const statusColors: Record<JobStatusEnum, string> = {
    planning: 'text-blue-400',
    validating: 'text-purple-400',
    architecting: 'text-yellow-400',
    rendering: 'text-orange-400',
    reviewing: 'text-pink-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
};

export function CouncilLog({ job, renderProgress = 0 }: { job: JobStatus | null, renderProgress?: number }) {
    if (!job) {
        return (
            <div className="font-mono text-sm text-neutral-600 p-4 border border-neutral-800 border-dashed rounded-lg bg-neutral-950/50">
                Waiting for input...
            </div>
        );
    }

    const LogLine = ({ children, color = 'text-neutral-300' }: { children: React.ReactNode, color?: string }) => (
        <div className="flex gap-3 mb-1">
            <span className="text-neutral-600 shrink-0">[{new Date().toLocaleTimeString([], { hour12: false })}]</span>
            <span className={color}>{children}</span>
        </div>
    );

    return (
        <div className="font-mono text-sm bg-neutral-950 rounded-lg border border-neutral-800 p-4 shadow-inner min-h-[300px] flex flex-col">
            <div className="flex items-center justify-between mb-4 border-b border-neutral-800 pb-2">
                <span className="text-neutral-400">Council Workflow</span>
                <div className="flex items-center gap-3">
                    {job.mode === 'mock' && (
                        <span className="bg-yellow-500/10 text-yellow-500 text-[10px] px-2 py-0.5 rounded border border-yellow-500/20 font-bold tracking-tighter">
                            MOCK
                        </span>
                    )}
                    <span className={`font-bold uppercase tracking-widest text-[10px] ${statusColors[job.status] || 'text-neutral-400'}`}>
                        {job.status}
                    </span>
                </div>
            </div>

            <div className="space-y-1 overflow-y-auto max-h-[400px] flex-grow">
                <LogLine>Job {job.job_id.slice(0, 8)}... initialized</LogLine>
                
                {job.plan && (
                    <LogLine color="text-blue-400">Analyst: Curriculum Plan generated</LogLine>
                )}

                {job.validation && (
                    <>
                        <LogLine color={job.validation.is_valid ? "text-purple-400" : "text-red-400"}>
                            Validator: {job.validation.is_valid ? "✅ Plan Verified" : "❌ Plan Rejected"}
                        </LogLine>
                        {job.validation.feedback && (
                            <div className="ml-16 mr-4 text-[11px] text-neutral-500 border-l-2 border-neutral-800 pl-3 py-1 mb-2 italic">
                                "{job.validation.is_valid ? job.validation.feedback : job.error}"
                            </div>
                        )}
                    </>
                )}

                {job.storyboard && (
                    <LogLine color="text-yellow-400">Architect: Visual Storyboard created ({job.storyboard.scenes.length} scenes)</LogLine>
                )}

                {job.manim_code && (
                    <LogLine color="text-orange-400">Animator: Manim Code generated</LogLine>
                )}

                {job.video_url && (
                    <LogLine color="text-green-400">Renderer: MP4 generated successfully</LogLine>
                )}

                {job.status === 'failed' && !job.validation && (
                    <LogLine color="text-red-400">System Error: {job.error}</LogLine>
                )}

                {job.status !== 'completed' && job.status !== 'failed' && (
                    <div className="space-y-3 mt-2">
                        <div className="flex items-center gap-2">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-ping" />
                            <span className="text-[10px] text-neutral-400 animate-pulse uppercase tracking-[0.2em]">Processing {job.status}...</span>
                        </div>
                        
                        {job.status === 'rendering' && (
                            <div className="ml-4 space-y-1">
                                <div className="h-1 w-full bg-neutral-900 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-indigo-500 transition-all duration-1000 ease-out"
                                        style={{ width: `${renderProgress}%` }}
                                    />
                                </div>
                                <div className="text-[9px] text-neutral-600 flex justify-between">
                                    <span>Manim Engine</span>
                                    <span>{Math.round(renderProgress)}%</span>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
