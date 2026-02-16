import { useEffect, useState, useMemo } from 'react';
import { listJobs, retryJob, deleteJob, getJobStatus, type JobSummary, type JobStatus } from '../../lib/api/client';
import { useDeveloperMode } from '../../lib/contexts/developer-mode';
import { StatusBadge } from '../ui/StatusBadge';
import { JobDetailPanel } from '../jobs/JobDetailPanel';
import { VideoPlayer } from '../ui/VideoPlayer';
import { 
    Play, 
    RotateCcw, 
    Download, 
    Trash2, 
    ChevronDown, 
    ChevronUp,
    Filter,
    ArrowUpDown,
    CheckSquare,
    Square,
    Clock,
    PlayCircle
} from 'lucide-react';
import { formatDuration, formatGenerationTime } from '../../lib/utils/duration-utils';
import { cn } from '../../lib/utils';

const formatTime = (isoString: string | null | undefined) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export function JobsPage() {
    const [jobs, setJobs] = useState<JobSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [, setError] = useState<string | null>(null);
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
            if (sortBy === 'cost') return ((b as any).cost || 0) - ((a as any).cost || 0);
            return 0;
        });
    }, [jobs, developerMode, statusFilter, sortBy]);

    // const uniqueModels = useMemo(() => Array.from(new Set(jobs.map(j => j.model_id).filter(Boolean))), [jobs]);

    useEffect(() => {
        loadJobs();
        const interval = setInterval(loadJobs, 5000); // Poll for updates
        return () => clearInterval(interval);
    }, []);

    const loadJobs = async () => {
        try {
            const response = await listJobs();
            setJobs(response.jobs);
            setError(null);
        } catch (err) {
            setError('Failed to load jobs');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = async (jobId: string) => {
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
    };

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
        setLoading(true);
        try {
            await Promise.all(Array.from(selectedJobIds).map(id => deleteJob(id)));
            setSelectedJobIds(new Set());
            await loadJobs();
        } catch (err) {
            console.error('Bulk delete failed', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading && jobs.length === 0) {
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
                            { label: 'Longest Duration', value: 'duration' },
                            { label: 'Highest Cost', value: 'cost' }
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
                            <th className="px-4 py-4 text-right">Model & Cost</th>
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
                                            deleteJob(job.job_id).then(loadJobs);
                                        }
                                    }}
                                    onRetry={() => retryJob(job.job_id).then(loadJobs)}
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

interface JobRowProps {
    job: JobSummary;
    isExpanded: boolean;
    isSelected: boolean;
    detail?: JobStatus;
    onToggleExpand: () => void;
    onToggleSelect: () => void;
    onDelete: () => void;
    onRetry: () => void;
    onPlay: () => void;
}

function JobRow({ job, isExpanded, isSelected, detail, onToggleExpand, onToggleSelect, onDelete, onRetry, onPlay }: JobRowProps) {
    const cost = (job as any).cost || 0;
    const metadata = (job as any).video_metadata || {};

    return (
        <>
            <tr className={cn(
                "group transition-all duration-200 cursor-pointer",
                isExpanded ? "bg-indigo-500/5" : "hover:bg-[var(--surface-border)]/20",
                isSelected && "bg-indigo-500/5"
            )} onClick={onToggleExpand}>
                <td className="pl-6 pr-4 py-5" onClick={(e) => { e.stopPropagation(); onToggleSelect(); }}>
                    <button className={cn("p-1 transition-colors", isSelected ? "text-indigo-500" : "text-[var(--text-muted)] group-hover:text-[var(--foreground)]")}>
                        {isSelected ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                    </button>
                </td>
                <td className="px-4 py-5">
                    <div className="w-20 aspect-video rounded-md bg-[var(--background)] border border-[var(--surface-border)] overflow-hidden relative shadow-inner">
                        {job.thumbnail_url ? (
                            <img src={job.thumbnail_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center">
                                <Play className="w-4 h-4 text-[var(--text-muted)]" />
                            </div>
                        )}
                    </div>
                </td>
                <td className="px-4 py-5 max-w-xs">
                    <span className="block font-semibold text-[var(--foreground)] truncate">{job.topic}</span>
                    <span className="block text-[10px] text-[var(--text-muted)] font-mono mt-0.5 uppercase tracking-tighter">{job.job_id.split('-')[0]}</span>
                </td>
                <td className="px-4 py-5">
                    <StatusBadge status={job.status as any} />
                </td>
                <td className="px-4 py-5 font-medium whitespace-nowrap">
                    <div className="flex flex-col">
                        <span className="text-[var(--foreground)] text-xs flex items-center gap-1.5">
                            <PlayCircle className="w-3 h-3 text-indigo-500/50" />
                            {formatDuration(Number(metadata.duration))}
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] flex items-center gap-1.5">
                            <Clock className="w-2.5 h-2.5" />
                            {formatGenerationTime(job.duration_seconds)}
                        </span>
                    </div>
                </td>
                <td className="px-4 py-5">
                    <div className="flex flex-col">
                        <span className="text-[var(--foreground)] font-medium text-xs">{metadata.resolution || '—'}</span>
                        <span className="text-[10px] text-[var(--text-muted)]">{metadata.file_size || ''}</span>
                    </div>
                </td>
                <td className="px-4 py-5 text-right">
                    <span className="block text-indigo-600 dark:text-indigo-400 font-bold">{cost > 0 ? `$${cost.toFixed(2)}` : '—'}</span>
                    <span className="block text-[10px] text-[var(--text-muted)] truncate">{job.model_id || '—'}</span>
                </td>
                <td className="px-4 py-5 text-right whitespace-nowrap">
                    <span className="block text-[var(--foreground)] opacity-80">{new Date(job.created_at).toLocaleDateString()}</span>
                    <span className="block text-[10px] text-[var(--text-muted)]">{formatTime(job.created_at)}</span>
                </td>
                <td className="pl-4 pr-6 py-5 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1 px-1">
                        {job.status === 'completed' && <ActionButton icon={<Play className="w-3.5 h-3.5" />} title="Play" onClick={onPlay} />}
                        {job.status === 'failed' && <ActionButton icon={<RotateCcw className="w-3.5 h-3.5" />} title="Retry" onClick={onRetry} />}
                        {job.status === 'completed' && <ActionButton icon={<Download className="w-3.5 h-3.5" />} title="Download" onClick={() => {}} />}
                        <ActionButton icon={<Trash2 className="w-3.5 h-3.5" />} title="Delete" variant="danger" onClick={onDelete} />
                        <button 
                            onClick={(e) => { e.stopPropagation(); onToggleExpand(); }}
                            className="ml-2 pl-2 border-l border-[var(--surface-border)] hover:text-[var(--foreground)] transition-colors"
                        >
                            {isExpanded ? <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />}
                        </button>
                    </div>
                </td>
            </tr>
            {isExpanded && (
                <tr>
                    <td colSpan={9} className="p-0 border-b border-[var(--surface-border)]">
                        {detail ? <JobDetailPanel job={detail} /> : (
                            <div className="p-12 text-center bg-[var(--surface)]/50">
                                <Loader2 className="w-6 h-6 text-indigo-500 animate-spin mx-auto mb-2" />
                                <span className="text-[var(--text-muted)] text-sm">Loading job artifacts...</span>
                            </div>
                        )}
                    </td>
                </tr>
            )}
        </>
    );
}

function ActionButton({ icon, title, onClick, variant = 'default' }: { icon: React.ReactNode; title: string, onClick: (e: React.MouseEvent) => void, variant?: 'default' | 'danger' }) {
    return (
        <button 
            title={title} 
            onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onClick(e);
            }}
            className={cn(
                "p-2 rounded-lg transition-all active:scale-95 shadow-sm",
                variant === 'danger' ? "hover:bg-red-500/10 hover:text-red-500 text-[var(--text-muted)]" : "hover:bg-indigo-500/10 hover:text-indigo-600 text-[var(--text-muted)]"
            )}
        >
            {icon}
        </button>
    );
}

function FilterSelect({ icon, value, onChange, options }: { icon: React.ReactNode, value: string, onChange: (v: string) => void, options: { label: string, value: string }[] }) {
    return (
        <div className="relative group">
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] group-hover:text-indigo-500 transition-colors pointer-events-none">
                {icon}
            </div>
            <select 
                value={value} 
                onChange={(e) => onChange(e.target.value)}
                className="pl-8 pr-10 py-2 bg-[var(--surface)] border border-[var(--surface-border)] rounded-xl text-xs font-bold text-[var(--text-muted)] focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 outline-none appearance-none cursor-pointer hover:border-[var(--surface-border)] transition-all shadow-sm"
            >
                {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none group-hover:text-indigo-500 transition-colors">
                <ChevronDown className="w-3.5 h-3.5" />
            </div>
        </div>
    );
}

function Loader2({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
        </svg>
    );
}
