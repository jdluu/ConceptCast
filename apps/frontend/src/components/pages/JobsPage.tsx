import { useState, useMemo, useCallback } from 'react';
import {
  retryJob,
  deleteJob,
  getJobStatus,
  type JobSummary,
  type JobStatus,
} from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useJobStore } from '@/lib/store/useJobStore';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { JobRow } from '@/components/jobs/JobRow';
import { useJobs } from '@/lib/hooks/useJobs';
import { Trash2, Filter, ArrowUpDown, CheckSquare, Square } from 'lucide-react';

export function JobsPage() {
  const { data, isPending, refetch } = useJobs();
  const jobs = data?.jobs ?? [];

  const { currentJob, resetJob } = useJobStore();

  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<Set<string>>(new Set());
  const [fullJobDetails, setFullJobDetails] = useState<Record<string, JobStatus>>({});
  const [playingJob, setPlayingJob] = useState<JobSummary | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setBy] = useState<'newest' | 'duration' | 'cost'>('newest');

  const { developerMode } = useDeveloperMode();

  const filteredJobs = useMemo(() => {
    let result = developerMode ? jobs : jobs.filter((job) => job.mode !== 'mock');

    if (statusFilter !== 'all') result = result.filter((j) => j.status === statusFilter);

    return result.toSorted((a, b) => {
      if (sortBy === 'newest')
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === 'duration')
        return (
          (Number((b as any).video_metadata?.duration) || 0) -
          (Number((a as any).video_metadata?.duration) || 0)
        );
      return 0;
    });
  }, [jobs, developerMode, statusFilter, sortBy]);

  const toggleExpand = useCallback(
    async (jobId: string) => {
      if (expandedJobId === jobId) {
        setExpandedJobId(null);
      } else {
        setExpandedJobId(jobId);
        if (!fullJobDetails[jobId]) {
          try {
            const details = await getJobStatus(jobId);
            setFullJobDetails((prev) => ({ ...prev, [jobId]: details }));
          } catch (error) {
            console.error('Failed to fetch job details', error);
          }
        }
      }
    },
    [expandedJobId, fullJobDetails],
  );

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
      setSelectedJobIds(new Set(filteredJobs.map((j) => j.job_id)));
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Delete ${selectedJobIds.size} jobs?`)) return;
    try {
      await Promise.all(Array.from(selectedJobIds).map((id) => deleteJob(id)));
      if (currentJob && selectedJobIds.has(currentJob.job_id)) {
        resetJob();
      }
      setSelectedJobIds(new Set());
      await refetch();
    } catch (error) {
      console.error('Bulk delete failed', error);
    }
  };

  if (isPending) {
    return <div className="p-8 text-[var(--text-muted)]">Loading jobs...</div>;
  }

  return (
    <div className="mx-auto max-w-[1400px] px-6 py-8 transition-colors duration-300">
      <header className="mb-10 flex flex-col justify-between gap-6 md:flex-row md:items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--foreground)]">
            Job History
          </h1>
          <p className="mt-1 text-[var(--text-muted)]">
            Monitor and manage your generation pipeline.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <FilterSelect
            icon={<Filter className="h-3.5 w-3.5" />}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { label: 'All Statuses', value: 'all' },
              { label: 'Completed', value: 'completed' },
              { label: 'Failed', value: 'failed' },
              { label: 'Running', value: 'rendering' },
            ]}
          />
          <FilterSelect
            icon={<ArrowUpDown className="h-3.5 w-3.5" />}
            value={sortBy}
            onChange={(v) => setBy(v as any)}
            options={[
              { label: 'Newest First', value: 'newest' },
              { label: 'Longest Duration', value: 'duration' },
            ]}
          />
          {selectedJobIds.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm font-bold text-red-500 transition-all hover:bg-red-500/20"
            >
              <Trash2 className="h-4 w-4" />
              Delete ({selectedJobIds.size})
            </button>
          )}
        </div>
      </header>

      <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] shadow-sm backdrop-blur-sm">
        <table className="w-full border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-[var(--surface-border)] bg-[var(--surface)] text-[11px] font-bold tracking-[0.1em] text-[var(--text-muted)] uppercase">
              <th className="w-10 py-4 pr-4 pl-6">
                <button
                  onClick={toggleSelectAll}
                  className="p-1 transition-colors hover:text-[var(--foreground)]"
                >
                  {selectedJobIds.size === filteredJobs.length && filteredJobs.length > 0 ? (
                    <CheckSquare className="h-4 w-4 text-indigo-500" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                </button>
              </th>
              <th className="px-4 py-4">Preview</th>
              <th className="px-4 py-4">Scene Name</th>
              <th className="px-4 py-4">Status</th>
              <th className="px-4 py-4">Duration</th>
              <th className="px-4 py-4">Output</th>
              <th className="px-4 py-4 text-right">Model</th>
              <th className="px-4 py-4 text-right">Created</th>
              <th className="py-4 pr-6 pl-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--surface-border)]/50">
            {filteredJobs.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-6 py-20 text-center">
                  <p className="font-medium text-[var(--text-muted)]">No production jobs found.</p>
                  <p className="mt-1 text-xs text-[var(--text-muted)] opacity-70">
                    Try changing your filters or starting a new project.
                  </p>
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
                    if (
                      confirm('Are you sure you want to delete this job and all its artifacts?')
                    ) {
                      deleteJob(job.job_id).then(() => {
                        if (currentJob?.job_id === job.job_id) {
                          resetJob();
                        }
                        refetch();
                      });
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
        <div className="animate-in fade-in fixed inset-0 z-50 flex items-center justify-center bg-black/95 p-6 backdrop-blur-sm duration-300">
          <div className="relative w-full max-w-5xl">
            <button
              onClick={() => setPlayingJob(null)}
              className="absolute -top-12 right-0 flex items-center gap-2 text-xs font-bold tracking-widest text-white/60 uppercase transition-colors hover:text-white"
            >
              Close
            </button>
            <div className="overflow-hidden rounded-2xl border border-white/10 bg-black shadow-2xl">
              <VideoPlayer src={playingJob.video_url!} />
            </div>
            <div className="mt-6 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">
                  {playingJob.topic || 'Untitled Concept'}
                </h3>
                <p className="mt-1 text-sm text-white/50">
                  {playingJob.model_id || 'ConceptCast Engine v1'}
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
