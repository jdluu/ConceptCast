import { useReducer, useMemo, useCallback } from 'react';
import { retryJob, deleteJob, getJobStatus, type JobStatus } from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useJobStore, selectJobActions } from '@/lib/store/useJobStore';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { FilterSelect } from '@/components/ui/FilterSelect';
import { Modal } from '@/components/ui/Common';
import { JobRow } from '@/components/jobs/JobRow';
import { useJobs } from '@/lib/hooks/useJobs';
import { Trash2, Filter, ArrowUpDown, CheckSquare, Square, ArrowLeftRight } from 'lucide-react';
import { useShallow } from 'zustand/react/shallow';

type JobsPageState = {
  expandedId: string | null;
  selectedIds: Set<string>;
  playingJob: JobStatus | null;
  expandedDetail: JobStatus | undefined;
  statusFilter: string;
  sortBy: 'newest' | 'oldest' | 'topic';
};

type JobsPageAction =
  | { type: 'setExpandedId'; id: string | null }
  | { type: 'setExpandedDetail'; detail: JobStatus | undefined }
  | { type: 'toggleSelect'; id: string }
  | { type: 'setSelectedIds'; ids: Set<string> }
  | { type: 'setPlayingJob'; job: JobStatus | null }
  | { type: 'setStatusFilter'; value: string }
  | { type: 'setSortBy'; value: 'newest' | 'oldest' | 'topic' };

function jobsPageReducer(state: JobsPageState, action: JobsPageAction): JobsPageState {
  switch (action.type) {
    case 'setExpandedId':
      return { ...state, expandedId: action.id };
    case 'setExpandedDetail':
      return { ...state, expandedDetail: action.detail };
    case 'toggleSelect': {
      const next = new Set(state.selectedIds);
      if (next.has(action.id)) next.delete(action.id);
      else next.add(action.id);
      return { ...state, selectedIds: next };
    }
    case 'setSelectedIds':
      return { ...state, selectedIds: action.ids };
    case 'setPlayingJob':
      return { ...state, playingJob: action.job };
    case 'setStatusFilter':
      return { ...state, statusFilter: action.value };
    case 'setSortBy':
      return { ...state, sortBy: action.value };
    default:
      return state;
  }
}

export function JobsPage() {
  const { data, isPending, refetch } = useJobs();
  const jobs = data?.jobs ?? [];
  const { developerMode } = useDeveloperMode();
  const { removeJob } = useJobStore(useShallow(selectJobActions));

  const [state, dispatch] = useReducer(jobsPageReducer, {
    expandedId: null,
    selectedIds: new Set<string>(),
    playingJob: null,
    expandedDetail: undefined,
    statusFilter: 'all',
    sortBy: 'newest',
  } satisfies JobsPageState);

  const filteredJobs = useMemo(() => {
    let result = [...jobs];
    if (!developerMode) {
      result = result.filter((j) => j.mode !== 'mock');
    }
    if (state.statusFilter !== 'all') {
      result = result.filter((j) => j.status === state.statusFilter);
    }
    return result.toSorted((a, b) => {
      if (state.sortBy === 'topic') return a.topic.localeCompare(b.topic);
      const timeA = new Date(a.created_at).getTime();
      const timeB = new Date(b.created_at).getTime();
      return state.sortBy === 'newest' ? timeB - timeA : timeA - timeB;
    });
  }, [jobs, state.statusFilter, state.sortBy, developerMode]);

  const toggleExpand = useCallback(
    async (jobId: string) => {
      if (state.expandedId === jobId) {
        dispatch({ type: 'setExpandedId', id: null });
        dispatch({ type: 'setExpandedDetail', detail: undefined });
      } else {
        dispatch({ type: 'setExpandedId', id: jobId });
        dispatch({ type: 'setExpandedDetail', detail: undefined });
        try {
          const detail = await getJobStatus(jobId);
          dispatch({ type: 'setExpandedDetail', detail });
        } catch (e) {
          console.error('Failed to fetch job details', e);
        }
      }
    },
    [state.expandedId],
  );

  const toggleSelect = (jobId: string) => {
    dispatch({ type: 'toggleSelect', id: jobId });
  };

  const toggleSelectAll = () => {
    if (state.selectedIds.size === filteredJobs.length) {
      dispatch({ type: 'setSelectedIds', ids: new Set() });
    } else {
      dispatch({ type: 'setSelectedIds', ids: new Set(filteredJobs.map((j) => j.job_id)) });
    }
  };

  const handleBatchDelete = async () => {
    if (confirm(`Delete ${state.selectedIds.size} jobs permanently?`)) {
      try {
        await Promise.all(
          Array.from(state.selectedIds).map(async (id) => {
            await deleteJob(id);
            removeJob(id);
          }),
        );
        dispatch({ type: 'setSelectedIds', ids: new Set() });
        refetch();
      } catch (e) {
        console.error('Batch deletion failed', e);
      }
    }
  };

  const handlePlay = async (jobId: string) => {
    try {
      const detail = await getJobStatus(jobId);
      dispatch({ type: 'setPlayingJob', job: detail });
    } catch (e) {
      console.error('Failed to fetch video for playback', e);
    }
  };

  if (isPending) {
    return <div className="text-text-muted p-8">Synchronizing with Council database...</div>;
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6">
      <header className="mb-10 flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <h1 className="text-foreground text-3xl font-bold tracking-tight">Generation Jobs</h1>
          <p className="text-text-muted mt-1">Manage and monitor your generation runs.</p>
        </div>

        <div className="flex w-full flex-col gap-3 md:w-auto md:flex-row md:flex-wrap md:items-center">
          <div className="w-full md:w-[220px]">
            <FilterSelect
              icon={<Filter className="h-4 w-4" />}
              value={state.statusFilter}
              onChange={(v) => dispatch({ type: 'setStatusFilter', value: v })}
              options={[
                { label: 'All Statuses', value: 'all' },
                { label: 'Completed', value: 'completed' },
                { label: 'Failed', value: 'failed' },
                { label: 'Processing', value: 'rendering' },
              ]}
            />
          </div>
          <div className="w-full md:w-[220px]">
            <FilterSelect
              icon={<ArrowUpDown className="h-4 w-4" />}
              value={state.sortBy}
              onChange={(v) => dispatch({ type: 'setSortBy', value: v as any })}
              options={[
                { label: 'Newest First', value: 'newest' },
                { label: 'Oldest First', value: 'oldest' },
                { label: 'Topic A-Z', value: 'topic' },
              ]}
            />
          </div>
          {state.selectedIds.size > 0 && (
            <button
              onClick={handleBatchDelete}
              className="border-destructive/20 bg-destructive/10 text-destructive hover:bg-destructive/20 flex items-center gap-2 rounded-xl border px-4 py-2 text-sm font-bold transition-all"
            >
              <Trash2 className="h-4 w-4" />
              Delete ({state.selectedIds.size})
            </button>
          )}
        </div>
      </header>

      <div className="text-text-muted mb-3 flex items-center gap-2 text-xs font-semibold sm:hidden">
        <ArrowLeftRight className="h-3.5 w-3.5 opacity-70" />
        Swipe to scroll
      </div>

      <div className="border-surface-border bg-surface custom-scrollbar overflow-x-auto rounded-2xl border shadow-xl">
        <table className="w-full min-w-[1000px] border-collapse text-left">
          <thead>
            <tr className="border-surface-border bg-surface/50 text-tiny text-text-muted border-b font-bold tracking-widest uppercase">
              <th className="py-4 pr-4 pl-6">
                <button
                  onClick={toggleSelectAll}
                  className="hover:text-foreground p-1 transition-colors"
                >
                  {state.selectedIds.size === filteredJobs.length && filteredJobs.length > 0 ? (
                    <CheckSquare className="text-council-active h-4 w-4" />
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
          <tbody className="divide-surface-border/50 divide-y">
            {filteredJobs.map((job) => (
              <JobRow
                key={job.job_id}
                job={job}
                isExpanded={state.expandedId === job.job_id}
                isSelected={state.selectedIds.has(job.job_id)}
                detail={state.expandedId === job.job_id ? state.expandedDetail : undefined}
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
                <td colSpan={9} className="text-text-muted py-20 text-center italic">
                  No generation runs found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Video Preview Modal */}
      <Modal
        isOpen={!!state.playingJob}
        onClose={() => dispatch({ type: 'setPlayingJob', job: null })}
        title={state.playingJob?.topic || 'Playback'}
      >
        {state.playingJob && (
          <div className="space-y-6">
            <div className="border-surface-border overflow-hidden rounded-xl border bg-black shadow-2xl">
              <VideoPlayer src={state.playingJob.video_url!} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-text-muted text-sm">
                  {state.playingJob.model_id || 'ConceptCast Engine v1'}
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
