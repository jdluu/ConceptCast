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

export function CouncilLog({ job }: { job: JobStatus | null }) {
    if (!job) {
        return (
            <div className="font-mono text-sm text-neutral-600 p-4 border border-neutral-800 border-dashed rounded-lg bg-neutral-950/50">
                Waiting for input...
            </div>
        );
    }

    return (
        <div className="font-mono text-sm bg-neutral-950 rounded-lg border border-neutral-800 p-4 shadow-inner min-h-[200px]">
            <div className="flex items-center justify-between mb-4 border-b border-neutral-800 pb-2">
                <span className="text-neutral-400">System Status</span>
                <div className="flex items-center gap-3">
                    {job.mode === 'mock' && (
                        <span className="bg-yellow-500/10 text-yellow-500 text-xs px-2 py-0.5 rounded border border-yellow-500/20 font-medium">
                            MOCK
                        </span>
                    )}
                    <span className={`font-bold ${statusColors[job.status] || 'text-neutral-400'}`}>
                        {job.status.toUpperCase()}
                    </span>
                </div>
            </div>

            <div className="space-y-2">
                <div className="flex gap-3">
                    <span className="text-neutral-600">[{new Date().toLocaleTimeString()}]</span>
                    <span className="text-neutral-300">Job initialized: {job.job_id}</span>
                </div>
                {job.error && (
                    <div className="flex gap-3 text-red-400">
                        <span className="text-neutral-600">[{new Date().toLocaleTimeString()}]</span>
                        <span>Error: {job.error}</span>
                    </div>
                )}
                {job.plan && (
                     <div className="flex gap-3 text-green-400">
                        <span className="text-neutral-600">[{new Date().toLocaleTimeString()}]</span>
                        <span>Plan generated: {job.plan.concept_title}</span>
                    </div>
                )}
                {job.status === 'reviewing' && (
                     <div className="flex gap-3 text-pink-400 animate-pulse">
                        <span className="text-neutral-600">[{new Date().toLocaleTimeString()}]</span>
                        <span>Awaiting User Review...</span>
                    </div>
                )}
            </div>
        </div>
    );
}
