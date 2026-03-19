import { useState, useMemo } from 'react';
import { Play, Search, Filter, Calendar } from 'lucide-react';
import { deleteJob, getJobStatus, type JobStatus } from '@/lib/api/client';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { Modal } from '@/components/ui/Common';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useLibrary } from '@/lib/hooks/useLibrary';
import { VideoCard } from '@/components/library/VideoCard';

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

  const handleDelete = async (jobId: string) => {
    if (confirm('Are you sure you want to delete this video from your library?')) {
      try {
        await deleteJob(jobId);
        refetch();
      } catch (error) {
        console.error('Failed to delete job', error);
      }
    }
  };

  if (isPending) {
    return <div className="text-text-muted p-8">Loading library...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 transition-colors duration-300 sm:px-6">
      <header className="mb-12">
        <h1 className="text-foreground mb-2 text-4xl font-bold tracking-tight">Library</h1>
        <p className="text-text-muted">
          Your collection of high-quality generated educational content.
        </p>
      </header>

      <div className="mb-10 flex flex-col gap-4 md:flex-row md:items-center">
        <div className="group relative w-full flex-1">
          <Search className="text-text-muted group-focus-within:text-council-active absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 transition-colors" />
          <input
            type="search"
            placeholder="Search your library..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border-surface-border bg-surface text-foreground placeholder:text-text-muted focus:border-council-active/50 focus:ring-council-active/50 w-full rounded-2xl border py-3 pr-4 pl-12 text-sm shadow-sm transition-all outline-none focus:ring-2"
          />
        </div>
        <div className="flex w-full flex-col gap-3 sm:flex-row md:w-auto">
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
        <div className="border-surface-border bg-surface/20 rounded-3xl border-2 border-dashed py-32 text-center">
          <div className="bg-surface mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full shadow-sm">
            <Play className="text-council-active h-8 w-8" />
          </div>
          <h3 className="text-foreground mb-2 text-xl font-bold">No videos found</h3>
          <p className="text-text-muted mx-auto max-w-xs">
            Once you complete a generation job, it will appear here in your permanent library.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
          {filteredJobs.map((job) => (
            <VideoCard key={job.job_id} job={job} onPlay={handlePlay} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {/* Video Modal */}
      <Modal
        isOpen={!!selectedJob}
        onClose={() => setSelectedJob(null)}
        title={selectedJob?.topic || 'Playback'}
      >
        {selectedJob && (
          <div className="space-y-6">
            <div className="border-surface-border overflow-hidden rounded-xl border bg-black shadow-2xl">
              <VideoPlayer src={selectedJob.video_url!} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-muted text-sm">
                  {selectedJob.model_id || 'ConceptCast Engine v1'}
                </p>
              </div>
              <button className="border-surface-border bg-surface text-foreground hover:bg-surface-border/20 rounded-xl border px-6 py-2.5 text-sm font-bold transition-all">
                Download HD
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
