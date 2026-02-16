import { useEffect, useState, useMemo } from 'react';
import { listJobs, getJobStatus, type JobSummary, type JobStatus, deleteJob } from '../../lib/api/client';
import { 
    Play, 
    Search, 
    Filter, 
    Trash2, 
    Download,
    Calendar,
    Clock,
    PlayCircle,
    ChevronDown
} from 'lucide-react';
import { useDeveloperMode } from '../../lib/contexts/developer-mode';
import { VideoPlayer } from '../ui/VideoPlayer';
import { formatDuration, formatGenerationTime } from '../../lib/utils/duration-utils';

export function LibraryPage() {
    const [jobs, setJobs] = useState<JobSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedJob, setSelectedJob] = useState<JobStatus | null>(null);
    const [sortBy, setBy] = useState<'latest' | 'oldest' | 'topic' | 'duration'>('latest');
    const [topicFilter, setTopicFilter] = useState('all');
    
    const { developerMode } = useDeveloperMode();
    
    useEffect(() => {
        loadLibrary();
    }, []);
    
    const loadLibrary = async () => {
        try {
            const data = await listJobs();
            const completedJobs = data.jobs.filter(j => j.status === 'completed');
            setJobs(completedJobs);
        } catch (err) {
            console.error('Failed to load library', err);
        } finally {
            setLoading(false);
        }
    };
    
    const uniqueTopics = useMemo(() => {
        const topics = new Set(jobs.map(j => j.topic));
        return Array.from(topics).sort();
    }, [jobs]);
    
    const filteredJobs = useMemo(() => {
        let result = developerMode ? jobs : jobs.filter(job => job.mode !== 'mock');
        
        if (search) {
            result = result.filter(j => j.topic.toLowerCase().includes(search.toLowerCase()));
        }
        
        if (topicFilter !== 'all') {
            result = result.filter(j => j.topic === topicFilter);
        }
        
        return result.sort((a, b) => {
            if (sortBy === 'latest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
            if (sortBy === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
            if (sortBy === 'topic') return a.topic.localeCompare(b.topic);
            if (sortBy === 'duration') return (Number(b.video_metadata?.duration) || 0) - (Number(a.video_metadata?.duration) || 0);
            return 0;
        });
    }, [jobs, search, developerMode, sortBy, topicFilter]);
    
    const handlePlay = async (jobId: string) => {
        try {
            const details = await getJobStatus(jobId);
            setSelectedJob(details);
        } catch (err) {
            console.error('Failed to fetch job for playback', err);
        }
    };
    
    if (loading) {
        return <div className="p-8 text-[var(--text-muted)]">Loading library...</div>;
    }
    
    return (
        <div className="max-w-7xl mx-auto px-6 transition-colors duration-300">
            <header className="mb-12">
                <h1 className="text-4xl font-bold text-[var(--foreground)] tracking-tight mb-2">Library</h1>
                <p className="text-[var(--text-muted)]">Your collection of high-quality generated educational content.</p>
            </header>
            
            <div className="flex flex-col md:flex-row gap-4 mb-10">
                <div className="relative flex-1 group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)] group-focus-within:text-indigo-500 transition-colors" />
                    <input
                        type="search"
                        placeholder="Search your library..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-11 pr-4 py-3 bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl text-[var(--foreground)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 outline-none transition-all shadow-sm"
                    />
                </div>
                <div className="flex gap-2">
                    <FilterSelect 
                        icon={<Calendar className="w-4 h-4" />} 
                        value={sortBy} 
                        onChange={(v) => setBy(v as any)}
                        options={[
                            { label: 'Latest First', value: 'latest' },
                            { label: 'Oldest First', value: 'oldest' },
                            { label: 'By Topic (A-Z)', value: 'topic' },
                            { label: 'Longest Duration', value: 'duration' }
                        ]}
                    />
                    <FilterSelect 
                        icon={<Filter className="w-4 h-4" />} 
                        value={topicFilter} 
                        onChange={setTopicFilter}
                        options={[
                            { label: 'All Topics', value: 'all' },
                            ...uniqueTopics.map(t => ({ label: t, value: t }))
                        ]}
                    />
                </div>
            </div>

            {filteredJobs.length === 0 ? (
                <div className="py-32 text-center border-2 border-dashed border-[var(--surface-border)] rounded-3xl bg-[var(--surface)]/20">
                    <div className="w-20 h-20 bg-[var(--surface)] rounded-full flex items-center justify-center mx-auto mb-6 shadow-sm">
                        <Play className="w-8 h-8 text-indigo-500" />
                    </div>
                    <h3 className="text-xl font-bold text-[var(--foreground)] mb-2">No videos found</h3>
                    <p className="text-[var(--text-muted)] max-w-xs mx-auto">
                        Once you complete a generation job, it will appear here in your permanent library.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredJobs.map((job) => (
                        <article 
                            key={job.job_id}
                            className="group relative bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden hover:border-indigo-500/50 hover:shadow-2xl hover:shadow-indigo-500/5 transition-all duration-500 flex flex-col shadow-sm"
                        >
                            {/* Thumbnail Container */}
                            <div className="aspect-video bg-[var(--background)] relative overflow-hidden shadow-inner">
                                {job.thumbnail_url ? (
                                    <img 
                                        src={job.thumbnail_url} 
                                        alt="" 
                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[var(--surface)] to-[var(--background)]">
                                        <Play className="w-12 h-12 text-[var(--text-muted)] opacity-20 group-hover:text-indigo-500/30 transition-colors" />
                                    </div>
                                )}
                                
                                {/* Overlay Gradient */}
                                <div className="absolute inset-0 bg-gradient-to-t from-[var(--surface)]/90 via-transparent to-transparent opacity-60 group-hover:opacity-100 transition-opacity" />
                                
                                {/* Duration Badge */}
                                <div className="absolute bottom-3 right-3 px-2 py-1 bg-black/80 backdrop-blur-md rounded text-[10px] font-bold text-white uppercase tracking-wider border border-white/10 flex items-center gap-1.5">
                                    <PlayCircle className="w-3 h-3 text-indigo-400" />
                                    {formatDuration(Number(job.video_metadata?.duration))}
                                </div>

                                {/* Hover Play Button */}
                                <button 
                                    onClick={() => handlePlay(job.job_id)}
                                    className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-4 group-hover:translate-y-0"
                                >
                                    <div className="w-20 h-20 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full flex items-center justify-center text-white shadow-2xl hover:scale-110 active:scale-95 transition-all">
                                        <Play className="w-8 h-8 fill-current" />
                                    </div>
                                </button>
                            </div>

                            {/* Content */}
                            <div className="p-6 flex-1 flex flex-col">
                                <h2 className="text-lg font-bold text-[var(--foreground)] mb-2 line-clamp-2 leading-snug group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                                    {job.topic}
                                </h2>
                                <div className="flex items-center gap-3 text-xs text-[var(--text-muted)] mb-6 flex-wrap">
                                    <span className="flex items-center gap-1">
                                        <Calendar className="w-3.5 h-3.5" />
                                        {new Date(job.created_at).toLocaleDateString()}
                                    </span>
                                    <span className="w-1 h-1 bg-[var(--surface-border)] rounded-full" />
                                    <span className="flex items-center gap-1">
                                        <Clock className="w-3.5 h-3.5 text-indigo-500/50" />
                                        {formatGenerationTime(job.duration_seconds)} gen
                                    </span>
                                    <span className="w-1 h-1 bg-[var(--surface-border)] rounded-full" />
                                    <span className="font-mono text-[10px] uppercase tracking-tighter text-[var(--text-muted)] opacity-80">{job.model_id?.split(':')[0] || 'Unknown'}</span>
                                </div>

                                <div className="mt-auto flex gap-3">
                                    <button 
                                        onClick={() => handlePlay(job.job_id)}
                                        className="flex-1 h-11 bg-indigo-600 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 hover:bg-indigo-700 transition-all active:scale-95 shadow-lg shadow-indigo-600/20"
                                    >
                                        <Play className="w-4 h-4 fill-current" />
                                        Play Now
                                    </button>
                                    <button className="w-11 h-11 bg-[var(--background)] border border-[var(--surface-border)] rounded-xl flex items-center justify-center text-[var(--text-muted)] hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-[var(--surface)] transition-all active:scale-95 shadow-sm">
                                        <Download className="w-4 h-4" />
                                    </button>
                                    <button 
                                        onClick={() => {
                                            if (confirm('Are you sure you want to delete this video from your library?')) {
                                                deleteJob(job.job_id).then(loadLibrary);
                                            }
                                        }}
                                        className="w-11 h-11 bg-[var(--background)] border border-[var(--surface-border)] rounded-xl flex items-center justify-center text-[var(--text-muted)] hover:text-red-500 hover:bg-red-500/10 hover:border-red-500/20 transition-all active:scale-95 shadow-sm"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            )}

            {/* Video Modal */}
            {selectedJob && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/95 backdrop-blur-sm animate-in fade-in duration-300">
                    <div className="relative w-full max-w-5xl">
                        <button 
                            onClick={() => setSelectedJob(null)}
                            className="absolute -top-12 right-0 text-white/60 hover:text-white transition-colors flex items-center gap-2 uppercase text-xs font-bold tracking-widest"
                        >
                            Close
                        </button>
                        <div className="rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-black">
                            <VideoPlayer src={selectedJob.video_url!} />
                        </div>
                        <div className="mt-6 flex items-center justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-white">{selectedJob.topic || 'Untitled Concept'}</h3>
                                <p className="text-white/50 text-sm mt-1">{selectedJob.model_id || 'ConceptCast Engine v1'}</p>
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

function FilterSelect({ icon, value, onChange, options }: { icon: React.ReactNode, value: string, onChange: (v: string) => void, options: { label: string, value: string }[] }) {
    return (
        <div className="relative group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)] group-hover:text-indigo-500 transition-colors pointer-events-none">
                {icon}
            </div>
            <select 
                value={value} 
                onChange={(e) => onChange(e.target.value)}
                className="pl-11 pr-10 py-3 bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl text-sm font-bold text-[var(--text-muted)] focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none appearance-none cursor-pointer hover:border-indigo-500 hover:text-[var(--foreground)] transition-all shadow-sm"
            >
                {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none group-hover:text-indigo-500 transition-colors">
                <ChevronDown className="w-4 h-4" />
            </div>
        </div>
    );
}
