import { useState, useMemo } from 'react';
import { Play, Search, Filter, Trash2, Download, Calendar, Clock, PlayCircle } from 'lucide-react';
import { deleteJob, getJobStatus, type JobStatus } from '@/lib/api/client';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useLibrary } from '@/lib/hooks/useLibrary';
import { formatDuration, formatGenerationTime } from '@/lib/utils/durationUtils';

export function LibraryPage() {
  const { data: jobs = [], isPending, refetch } = useLibrary();

  const [search, setSearch] = useState('');
  const [selectedJob, setSelectedJob] = useState<JobStatus | null>(null);
  const [sortBy, setBy] = useState<'latest' | 'oldest' | 'topic' | 'duration'>('latest');
  const [topicFilter, setTopicFilter] = useState('all');

  const { developerMode } = useDeveloperMode();

  const uniqueTopics = useMemo(() => {
    const topics = new Set(jobs.map((j) => j.topic));
    return [...topics].toSorted();
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    let result = developerMode ? jobs : jobs.filter((job) => job.mode !== 'mock');

    if (search) {
      result = result.filter((j) => j.topic.toLowerCase().includes(search.toLowerCase()));
    }

    if (topicFilter !== 'all') {
      result = result.filter((j) => j.topic === topicFilter);
    }

    return result.toSorted((a, b) => {
      if (sortBy === 'latest')
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === 'oldest')
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      if (sortBy === 'topic') return a.topic.localeCompare(b.topic);
      if (sortBy === 'duration')
        return (
          (Number(b.video_metadata?.duration) || 0) - (Number(a.video_metadata?.duration) || 0)
        );
      return 0;
    });
  }, [jobs, search, developerMode, sortBy, topicFilter]);

  const handlePlay = async (jobId: string) => {
    try {
      const details = await getJobStatus(jobId);
      setSelectedJob(details);
    } catch (error) {
      console.error('Failed to fetch job for playback', error);
    }
  };

  if (isPending) {
    return <div className="p-8 text-[var(--text-muted)]">Loading library...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-6 transition-colors duration-300">
      <header className="mb-12">
        <h1 className="mb-2 text-4xl font-bold tracking-tight text-[var(--foreground)]">Library</h1>
        <p className="text-[var(--text-muted)]">
          Your collection of high-quality generated educational content.
        </p>
      </header>

      <div className="mb-10 flex flex-col items-center gap-4 md:flex-row">
        <div className="group relative w-full flex-1">
          <Search className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-[var(--text-muted)] transition-colors group-focus-within:text-indigo-500" />
          <input
            type="search"
            placeholder="Search your library..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] py-3 pr-4 pl-12 text-sm text-[var(--foreground)] shadow-sm transition-all outline-none placeholder:text-[var(--text-muted)] focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/50"
          />
        </div>
        <div className="flex w-full gap-3 md:w-auto">
          <FilterSelect
            icon={<Calendar className="h-4 w-4" />}
            value={sortBy}
            onChange={(v) => setBy(v as any)}
            options={[
              { label: 'Latest First', value: 'latest' },
              { label: 'Oldest First', value: 'oldest' },
              { label: 'By Topic (A-Z)', value: 'topic' },
              { label: 'Longest Duration', value: 'duration' },
            ]}
          />
          <FilterSelect
            icon={<Filter className="h-4 w-4" />}
            value={topicFilter}
            onChange={setTopicFilter}
            options={[
              { label: 'All Topics', value: 'all' },
              ...uniqueTopics.map((t) => ({ label: t, value: t })),
            ]}
          />
        </div>
      </div>

      {filteredJobs.length === 0 ? (
        <div className="rounded-3xl border-2 border-dashed border-[var(--surface-border)] bg-[var(--surface)]/20 py-32 text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-[var(--surface)] shadow-sm">
            <Play className="h-8 w-8 text-indigo-500" />
          </div>
          <h3 className="mb-2 text-xl font-bold text-[var(--foreground)]">No videos found</h3>
          <p className="mx-auto max-w-xs text-[var(--text-muted)]">
            Once you complete a generation job, it will appear here in your permanent library.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {filteredJobs.map((job) => (
            <article
              key={job.job_id}
              className="group relative flex flex-col overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] shadow-sm transition-all duration-500 hover:border-indigo-500/50 hover:shadow-2xl hover:shadow-indigo-500/5"
            >
              {/* Thumbnail Container */}
              <div className="relative aspect-video overflow-hidden bg-[var(--background)] shadow-inner">
                {job.thumbnail_url ? (
                  <img
                    src={job.thumbnail_url}
                    alt=""
                    className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-[var(--surface)] to-[var(--background)]">
                    <Play className="h-12 w-12 text-[var(--text-muted)] opacity-20 transition-colors group-hover:text-indigo-500/30" />
                  </div>
                )}

                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-[var(--surface)]/90 via-transparent to-transparent opacity-60 transition-opacity group-hover:opacity-100" />

                {/* Duration Badge */}
                <div className="absolute right-3 bottom-3 flex items-center gap-1.5 rounded border border-white/10 bg-black/80 px-2 py-1 text-[10px] font-bold tracking-wider text-white uppercase backdrop-blur-md">
                  <PlayCircle className="h-3 w-3 text-indigo-400" />
                  {formatDuration(Number(job.video_metadata?.duration))}
                </div>

                {/* Hover Play Button */}
                <button
                  onClick={() => handlePlay(job.job_id)}
                  className="absolute inset-0 flex translate-y-4 transform items-center justify-center opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100"
                >
                  <div className="flex h-20 w-20 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white shadow-2xl backdrop-blur-xl transition-all hover:scale-110 active:scale-95">
                    <Play className="h-8 w-8 fill-current" />
                  </div>
                </button>
              </div>

              {/* Content */}
              <div className="flex flex-1 flex-col p-6">
                <h2 className="mb-2 line-clamp-2 text-lg leading-snug font-bold text-[var(--foreground)] transition-colors group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                  {job.topic}
                </h2>
                <div className="mb-6 flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)]">
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {new Date(job.created_at).toLocaleDateString()}
                  </span>
                  <span className="h-1 w-1 rounded-full bg-[var(--surface-border)]" />
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5 text-indigo-500/50" />
                    {formatGenerationTime(job.duration_seconds)} gen
                  </span>
                  <span className="h-1 w-1 rounded-full bg-[var(--surface-border)]" />
                  <span className="font-mono text-[10px] tracking-tighter text-[var(--text-muted)] uppercase opacity-80">
                    {job.model_id?.split(':')[0] || 'Unknown'}
                  </span>
                </div>

                <div className="mt-auto flex gap-3">
                  <button
                    onClick={() => handlePlay(job.job_id)}
                    className="flex h-11 flex-1 items-center justify-center gap-2 rounded-xl bg-indigo-600 text-sm font-bold text-white shadow-lg shadow-indigo-600/20 transition-all hover:bg-indigo-700 active:scale-95"
                  >
                    <Play className="h-4 w-4 fill-current" />
                    Play Now
                  </button>
                  <button className="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--surface-border)] bg-[var(--background)] text-[var(--text-muted)] shadow-sm transition-all hover:bg-[var(--surface)] hover:text-indigo-600 active:scale-95 dark:hover:text-indigo-400">
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (
                        confirm('Are you sure you want to delete this video from your library?')
                      ) {
                        deleteJob(job.job_id).then(() => refetch());
                      }
                    }}
                    className="flex h-11 w-11 items-center justify-center rounded-xl border border-[var(--surface-border)] bg-[var(--background)] text-[var(--text-muted)] shadow-sm transition-all hover:border-red-500/20 hover:bg-red-500/10 hover:text-red-500 active:scale-95"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Video Modal */}
      {selectedJob && (
        <div className="animate-in fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-6 backdrop-blur-sm duration-300">
          <div className="relative w-full max-w-5xl">
            <button
              onClick={() => setSelectedJob(null)}
              className="absolute -top-12 right-0 flex items-center gap-2 text-xs font-bold tracking-widest text-white/60 uppercase transition-colors hover:text-white"
            >
              Close
            </button>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl">
              <VideoPlayer src={selectedJob.video_url!} />
            </div>
            <div className="mt-6 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">
                  {selectedJob.topic || 'Untitled Concept'}
                </h3>
                <p className="mt-1 text-sm text-white/50">
                  {selectedJob.model_id || 'ConceptCast Engine v1'}
                </p>
              </div>
              <div className="flex gap-4">
                <button className="rounded-xl border border-white/10 bg-white/10 px-6 py-2.5 text-sm font-bold text-white transition-all hover:bg-white/20">
                  Download HD
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
