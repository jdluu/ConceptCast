import { useState, useMemo, useCallback } from 'react';
import {
  retryJob,
  deleteJob,
  getJobStatus,
  type JobStatus,
} from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useJobStore, selectJobActions } from '@/lib/store/useJobStore';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { Modal } from '@/components/ui/Common';
import { JobRow } from '@/components/jobs/JobRow';
import { useJobs } from '@/lib/hooks/useJobs';
import { Trash2, Filter, ArrowUpDown, CheckSquare, Square } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';

export function JobsPage() {
  const { data, isPending, refetch } = useJobs();
  const jobs = data?.jobs ?? [];
  const { developerMode } = useDeveloperMode();
  const { removeJob } = useJobStore(useShallow(selectJobActions));

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [playingJob, setPlayingJob] = useState<JobStatus | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<JobStatus | undefined>();

  // Filter & Sort State
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'topic'>('newest');

  const filteredJobs = useMemo(() => {
    let result = [...jobs];
    if (!developerMode) {
      result = result.filter((j) => j.mode !== 'mock');
    }
    if (statusFilter !== 'all') {
      result = result.filter((j) => j.status === statusFilter);
    }
    return result.toSorted((a, b) => {
      if (sortBy === 'topic') return a.topic.localeCompare(b.topic);
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return sortBy === 'newest' ? timeB - timeA : timeA - timeB;
    });
  }, [jobs, statusFilter, sortBy, developerMode]);

  const toggleExpand = useCallback(
    async (jobId: string) => {
      if (expandedId === jobId) {
        setExpandedId(null);
        setExpandedDetail(undefined);
      } else {
        setExpandedId(jobId);
        setExpandedDetail(undefined);
        try {
          const detail = await getJobStatus(jobId);
          setExpandedDetail(detail);
        } catch (e) {
          console.error('Failed to fetch job details', e);
        }
      }
    },
    [expandedId],
  );

  const toggleSelect = (jobId: string) => {
    const next = new Set(selectedIds);
    if (next.has(jobId)) next.delete(jobId);
    else next.add(jobId);
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === filteredJobs.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(filteredJobs.map((j) => j.job_id)));
  };

  const handleBatchDelete = async () => {
    if (confirm(`Delete ${selectedIds.size} jobs permanently?`)) {
      try {
        await Promise.all(
          Array.from(selectedIds).map(async (id) => {
            await deleteJob(id);
            removeJob(id);
          }),
        );
        setSelectedIds(new Set());
        refetch();
      } catch (e) {
        console.error('Batch deletion failed', e);
      }
    }
  };

  const handlePlay = async (jobId: string) => {
    try {
      const detail = await getJobStatus(jobId);
      setPlayingJob(detail);
    } catch (e) {
      console.error('Failed to fetch video for playback', e);
    }
  };

  if (isPending) {
    return <div className="p-8 text-text-muted">Synchronizing with Council database...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-6">
      <header className="mb-10 flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Orchestration Jobs</h1>
          <p className="mt-1 text-text-muted">Manage and monitor your pedagogical pipelines.</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <FilterSelect
            icon={<Filter className="h-4 w-4" />}
            value={statusFilter}
            onChange={setStatusFilter}
            options={[
              { label: 'All Statuses', value: 'all' },
              { label: 'Completed', value: 'completed' },
              { label: 'Failed', value: 'failed' },
              { label: 'Processing', value: 'rendering' },
            ]}
          />
          <FilterSelect
            icon={<ArrowUpDown className="h-4 w-4" />}
            value={sortBy}
            onChange={(v) => setSortBy(v as any)}
            options={[
              { label: 'Newest First', value: 'newest' },
              { label: 'Oldest First', value: 'oldest' },
              { label: 'Topic A-Z', value: 'topic' },
            ]}
          />
          {selectedIds.size > 0 && (
            <button
              onClick={handleBatchDelete}
              className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-2 text-sm font-bold text-destructive transition-all hover:bg-destructive/20"
            >
              <Trash2 className="h-4 w-4" />
              Delete ({selectedIds.size})
            </button>
          )}
        </div>
      </header>

      <div className="overflow-hidden rounded-2xl border border-surface-border bg-surface shadow-xl">
        <table className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-surface-border bg-surface/50 text-tiny font-bold tracking-widest text-text-muted uppercase">
              <th className="py-4 pr-4 pl-6">
                <button
                  onClick={toggleSelectAll}
                  className="p-1 transition-colors hover:text-foreground"
                >
                  {selectedIds.size === filteredJobs.length && filteredJobs.length > 0 ? (
                    <CheckSquare className="h-4 w-4 text-council-active" />
                  ) : (
                    <Square className="h-4 w-4" />
                  )}
                </button>
              </th>
              <th className="px-4 py-4">Preview</th>
              <th className="px-4 py-4">Topic & ID</th>
              <th className="px-4 py-4">Status</th>
              <th className="px-4 py-4">Resources</th>
              <th className="px-4 py-4">Format</th>
              <th className="px-4 py-4 text-right">Model</th>
              <th className="px-4 py-4 text-right">Timestamp</th>
              <th className="py-4 pr-6 pl-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border/50">
            {filteredJobs.map((job) => (
              <JobRow
                key={job.job_id}
                job={job}
                isExpanded={expandedId === job.job_id}
                isSelected={selectedIds.has(job.job_id)}
                detail={expandedId === job.job_id ? expandedDetail : undefined}
                onToggleExpand={() => toggleExpand(job.job_id)}
                onToggleSelect={() => toggleSelect(job.job_id)}
                onDelete={async () => {
                  if (confirm('Delete this job?')) {
                    await deleteJob(job.job_id);
                    removeJob(job.job_id);
                    refetch();
                  }
                }}
                onRetry={async () => {
                  await retryJob(job.job_id);
                  refetch();
                }}
                onPlay={() => handlePlay(job.job_id)}
              />
            ))}
            {filteredJobs.length === 0 && (
              <tr>
                <td colSpan={9} className="py-20 text-center text-text-muted italic">
                  No orchestration records found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Video Preview Modal */}
      <Modal
        isOpen={!!playingJob}
        onClose={() => setPlayingJob(null)}
        title={playingJob?.topic || 'Playback'}
      >
        {playingJob && (
          <div className="space-y-6">
            <div className="overflow-hidden rounded-xl border border-surface-border bg-black shadow-2xl">
              <VideoPlayer src={playingJob.video_url!} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-muted">
                  {playingJob.model_id || 'ConceptCast Engine v1'}
                </p>
              </div>
              <button className="rounded-xl border border-surface-border bg-surface px-6 py-2.5 text-sm font-bold text-foreground transition-all hover:bg-surface-border/20">
                Download HD
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
