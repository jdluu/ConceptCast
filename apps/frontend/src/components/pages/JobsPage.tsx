import { useState, useMemo, useCallback } from 'react';
import { retryJob, deleteJob, getJobStatus, type JobSummary, type JobStatus } from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { JobRow } from '@/components/jobs/JobRow';
import { useJobs } from '@/lib/hooks/useJobs';
import { 
    Trash2, 
    Filter,
    ArrowUpDown,
    CheckSquare,
    Square
} from 'lucide-react';

export function JobsPage() {
    const { data, isPending, refetch } = useJobs();
    const jobs = data?.jobs ?? [];

    const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
    const [selectedJobIds, setSelectedJobIds] = useState<Set<string>>(new Set());
    const [fullJobDetails, setFullJobDetails] = useState<Record<string, JobStatus>>({});
    const [playingJob, setPlayingJob] = useState<JobSummary | null>(null);
    
    // Filters
    const [statusFilter, setStatusFilter] = useState('all');
    const [sortBy, setBy] = useState<'newest' | 'duration' | 'cost'>('newest');

    const { developerMode } = useDeveloperMode();

    const filteredJobs = useMemo(() => {
        let result = developerMode ? jobs : jobs.filter(job => job.mode !== 'mock');
        
        if (statusFilter !== 'all') result = result.filter(j => j.status === statusFilter);
        
        return result.sort((a, b) => {
            if (sortBy === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            if (sortBy === 'duration') return (Number((b as any).video_metadata?.duration) || 0) - (Number((a as any).video_metadata?.duration) || 0);
            return 0;
        });
    }, [jobs, developerMode, statusFilter, sortBy]);

    const toggleExpand = useCallback(async (jobId: string) => {
        if (expandedJobId === jobId) {
            setExpandedJobId(null);
        } else {
            setExpandedJobId(jobId);
            if (!fullJobDetails[jobId]) {
                try {
                    const details = await getJobStatus(jobId);
                    setFullJobDetails(prev => ({ ...prev, [jobId]: details }));
                } catch (err) {
                    console.error('Failed to fetch job details', err);
                }
            }
        }
    }, [expandedJobId, fullJobDetails]);

    const toggleSelect = (jobId: string) => {
        const next = new Set(selectedJobIds);
        if (next.has(jobId)) next.delete(jobId);
        else next.add(jobId);
        setSelectedJobIds(next);
    };

    const toggleSelectAll = () => {
        if (selectedJobIds.size === filteredJobs.length) {
            setSelectedJobIds(new Set());
        } else {
            setSelectedJobIds(new Set(filteredJobs.map(j => j.job_id)));
        }
    };

    const handleBulkDelete = async () => {
        if (!confirm(`Delete ${selectedJobIds.size} jobs?`)) return;
        try {
            await Promise.all(Array.from(selectedJobIds).map(id => deleteJob(id)));
            setSelectedJobIds(new Set());
            await refetch();
        } catch (err) {
            console.error('Bulk delete failed', err);
        }
    };

    if (isPending) {
        return <div className="p-8 text-[var(--text-muted)]">Loading jobs...</div>;
    }

    return (
        <div className="max-w-[1400px] mx-auto px-6 py-8 transition-colors duration-300">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">Job History</h1>
                    <p className="text-[var(--text-muted)] mt-1">Monitor and manage your generation pipeline.</p>
                </div>
                
                <div className="flex flex-wrap items-center gap-3">
                    <FilterSelect 
                        icon={<Filter className="w-3.5 h-3.5" />} 
                        value={statusFilter} 
                        onChange={setStatusFilter}
                        options={[
                            { label: 'All Statuses', value: 'all' },
                            { label: 'Completed', value: 'completed' },
                            { label: 'Failed', value: 'failed' },
                            { label: 'Running', value: 'rendering' }
                        ]}
                    />
                    <FilterSelect 
                        icon={<ArrowUpDown className="w-3.5 h-3.5" />} 
                        value={sortBy} 
                        onChange={(v) => setBy(v as any)}
                        options={[
                            { label: 'Newest First', value: 'newest' },
                            { label: 'Longest Duration', value: 'duration' }
                        ]}
                    />
                    {selectedJobIds.size > 0 && (
                        <button 
                            onClick={handleBulkDelete}
                            className="bg-red-500/10 text-red-500 border border-red-500/20 px-4 py-2 rounded-xl text-sm font-bold hover:bg-red-500/20 transition-all flex items-center gap-2"
                        >
                            <Trash2 className="w-4 h-4" />
                            Delete ({selectedJobIds.size})
                        </button>
                    )}
                </div>
            </header>

            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden shadow-sm backdrop-blur-sm">
                <table className="w-full text-left text-sm border-collapse">
                    <thead>
                        <tr className="bg-[var(--surface)] border-b border-[var(--surface-border)] text-[11px] uppercase tracking-[0.1em] font-bold text-[var(--text-muted)]">
                            <th className="pl-6 pr-4 py-4 w-10">
                                <button onClick={toggleSelectAll} className="p-1 hover:text-[var(--foreground)] transition-colors">
                                    {selectedJobIds.size === filteredJobs.length && filteredJobs.length > 0 ? <CheckSquare className="w-4 h-4 text-indigo-500" /> : <Square className="w-4 h-4" />}
                                </button>
                            </th>
                            <th className="px-4 py-4">Preview</th>
                            <th className="px-4 py-4">Scene Name</th>
                            <th className="px-4 py-4">Status</th>
                            <th className="px-4 py-4">Duration</th>
                            <th className="px-4 py-4">Output</th>
                            <th className="px-4 py-4 text-right">Model</th>
                            <th className="px-4 py-4 text-right">Created</th>
                            <th className="pl-4 pr-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--surface-border)]/50">
                        {filteredJobs.length === 0 ? (
                            <tr>
                                <td colSpan={9} className="px-6 py-20 text-center">
                                    <p className="text-[var(--text-muted)] font-medium">No production jobs found.</p>
                                    <p className="text-[var(--text-muted)] text-xs mt-1 opacity-70">Try changing your filters or starting a new project.</p>
                                </td>
                            </tr>
                        ) : (
                            filteredJobs.map((job) => (
                                <JobRow 
                                    key={job.job_id}
                                    job={job}
                                    isExpanded={expandedJobId === job.job_id}
                                    isSelected={selectedJobIds.has(job.job_id)}
                                    detail={fullJobDetails[job.job_id]}
                                    onToggleExpand={() => toggleExpand(job.job_id)}
                                    onToggleSelect={() => toggleSelect(job.job_id)}
                                    onDelete={() => {
                                        if (confirm('Are you sure you want to delete this job and all its artifacts?')) {
                                            deleteJob(job.job_id).then(() => refetch());
                                        }
                                    }}
                                    onRetry={() => retryJob(job.job_id).then(() => refetch())}
                                    onPlay={() => setPlayingJob(job)}
                                />
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Video Preview Modal */}
            {playingJob && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="relative w-full max-w-5xl">
                        <button 
                            onClick={() => setPlayingJob(null)}
                            className="absolute -top-12 right-0 text-white/60 hover:text-white transition-colors flex items-center gap-2 uppercase text-xs font-bold tracking-widest"
                        >
                            Close
                        </button>
                        <div className="rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-black">
                            <VideoPlayer src={playingJob.video_url!} />
                        </div>
                        <div className="mt-6 flex items-center justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-white">{playingJob.topic || 'Untitled Concept'}</h3>
                                <p className="text-white/50 text-sm mt-1">{playingJob.model_id || 'ConceptCast Engine v1'}</p>
                            </div>
                            <div className="flex gap-4">
                                <button className="px-6 py-2.5 bg-white/10 border border-white/10 rounded-xl text-sm font-bold text-white hover:bg-white/20 transition-all">Download HD</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
