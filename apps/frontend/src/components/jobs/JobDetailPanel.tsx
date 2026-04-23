import React from 'react';
import { JobStatus, ThoughtLog, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { CurriculumPlanView } from '@/components/orchestration/artifacts/CurriculumPlanView';
import { StoryboardView } from '@/components/orchestration/artifacts/StoryboardView';
import { ArtifactBadge } from '@/components/orchestration/artifacts/ArtifactCommon';
import { format } from 'date-fns';
import { formatDuration } from '@/lib/utils/durationUtils';
import { Loader2 } from 'lucide-react';
import { useJobEvents } from '@/lib/hooks/useJobEvents';
import { LazyMotion, domAnimation } from 'motion/react';
import * as m from 'motion/react-m';

interface JobDetailPanelProps {
  jobId: string;
  initialData?: JobStatus;
}

/**
 * Detailed view of a job's artifacts and metadata.
 * Uses SSE via useJobEvents for real-time updates.
 */
export function JobDetailPanel({ jobId }: JobDetailPanelProps) {
  const { jobStatus: job, connectionState } = useJobEvents(jobId);

  if (!job) {
    return (
      <div className="bg-surface/50 flex flex-col items-center justify-center p-12 text-center">
        <Loader2 className="text-council-active mb-2 h-6 w-6 animate-spin" />
        <span className="text-text-muted text-sm">
          {connectionState === 'connecting' ? 'Connecting to stream...' : 'Fetching job details...'}
        </span>
      </div>
    );
  }

  const topic = job.topic || 'Unknown Topic';
  const audience = job.target_audience || 'General';

  return (
    <div className="animate-in fade-in slide-in-from-top-4 border-surface-border bg-surface border-t p-8 duration-300">
      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12">
        {/* Left Column: Preview & Metadata */}
        <div className="space-y-6 lg:col-span-5">
          <div className="flex items-center justify-between">
            <h3 className="text-text-muted text-xs font-bold tracking-[0.2em] uppercase">
              Video Preview
            </h3>
            <div className="flex items-center gap-2">
              {job.status === 'rendering' && (
                <div className="mr-2 flex items-center gap-2">
                  <div className="bg-surface-border h-1.5 w-24 overflow-hidden rounded-full">
                    <m.div
                      initial={{ width: 0 }}
                      animate={{ width: `${job.render_progress}%` }}
                      className="bg-council-active h-full"
                    />
                  </div>
                  <span className="text-council-active font-mono text-[10px] font-bold">
                    {Math.round(job.render_progress)}%
                  </span>
                </div>
              )}
              <span
                className={`text-nano rounded-md px-2 py-0.5 font-bold tracking-widest uppercase ${job.mode === 'mock' ? 'bg-warning/10 text-warning' : 'bg-info/10 text-info'}`}
              >
                {job.mode}
              </span>
              <StatusBadge status={job.status} />
            </div>
          </div>
          {job.video_url ? (
            <div className="border-surface-border shadow-council-active/10 overflow-hidden rounded-2xl border shadow-2xl">
              <VideoPlayer src={job.video_url} />
            </div>
          ) : (
            <div className="border-surface-border bg-background/50 flex aspect-video items-center justify-center rounded-2xl border border-dashed">
              <span className="text-text-muted text-sm italic">Video not yet rendered</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <DataCard
              label="Model"
              value={job.model_id || 'Unknown'}
              subValue={job.provider || ''}
            />
            <DataCard label="Format" value="1080p (Full HD)" subValue="60 FPS Premium" />
            <DataCard
              label="Timeline"
              value={job.started_at ? format(new Date(job.started_at), 'PPP') : 'Pending'}
              subValue={
                job.status !== 'completed' && job.status !== 'failed' && job.current_step
                  ? `Active: ${job.current_step}`
                  : job.started_at
                    ? format(new Date(job.started_at), 'p')
                    : ''
              }
            />
            <DataCard
              label="Execution"
              value={formatDuration(job.duration_seconds)}
              subValue={job.retry_count > 0 ? `${job.retry_count} retries` : 'First attempt'}
            />
            <DataCard
              label="Resource Cost"
              value={`$${job.cost.toFixed(4)}`}
              subValue="Estimated credits"
            />
          </div>
        </div>

        {/* Right Column: Prompt, Code, Artifacts */}
        <div className="space-y-6 lg:col-span-7">
          <TabsSection
            tabs={[
              {
                id: 'prompt',
                label: 'Prompt',
                content: (
                  <PromptView topic={topic} userPrompt={job.user_prompt} audience={audience} />
                ),
              },
              {
                id: 'plan',
                label: 'Curriculum',
                content: (
                  <div className="scrollbar-thin scrollbar-thumb-surface-border max-h-[600px] overflow-y-auto pr-2">
                    <CurriculumPlanView
                      plan={job.plan as CurriculumPlan}
                      status={job.status}
                      onViewFull={() => {}}
                    />
                  </div>
                ),
              },
              {
                id: 'storyboard',
                label: 'Visuals',
                content: (
                  <div className="scrollbar-thin scrollbar-thumb-surface-border max-h-[600px] overflow-y-auto pr-2">
                    <StoryboardView storyboard={job.storyboard as Storyboard} status={job.status} />
                  </div>
                ),
              },
              { id: 'code', label: 'Script', content: <CodeView code={job.manim_code} /> },
              {
                id: 'thoughts',
                label: 'Stream',
                content: <ThoughtsView thoughts={job.streamed_thoughts} />,
              },
            ]}
          />
        </div>
      </div>

      {job.error && (
        <div className="border-destructive/20 bg-destructive/5 shadow-destructive/10 mt-8 rounded-xl border p-4 shadow-sm">
          <h4 className="text-destructive mb-1 text-xs font-bold tracking-widest uppercase">
            Execution Error
          </h4>
          <p className="text-destructive dark:text-destructive font-mono text-sm whitespace-pre-wrap">
            {job.error}
          </p>
        </div>
      )}
    </div>
  );
}

function DataCard({ label, value, subValue }: { label: string; value: string; subValue?: string }) {
  return (
    <div className="border-surface-border bg-background/30 rounded-xl border p-4 shadow-sm">
      <ArtifactBadge>{label}</ArtifactBadge>
      <span className="text-foreground block truncate text-sm font-bold" title={value}>
        {value}
      </span>
      {subValue && (
        <span className="text-tiny text-text-muted block truncate opacity-60">{subValue}</span>
      )}
    </div>
  );
}

function PromptView({
  topic,
  userPrompt,
  audience,
}: {
  topic: string;
  userPrompt?: string | null;
  audience: string | null | undefined;
}) {
  return (
    <div className="min-h-xs border-surface-border bg-background/30 space-y-6 rounded-2xl border p-6">
      <div>
        <ArtifactBadge variant="active">Refined Topic</ArtifactBadge>
        <p className="text-foreground mt-1 text-sm font-bold">{topic}</p>
      </div>
      {userPrompt && (
        <div>
          <ArtifactBadge>Original Request</ArtifactBadge>
          <p className="text-text-muted mt-1 text-sm leading-relaxed">{userPrompt}</p>
        </div>
      )}
      <div>
        <ArtifactBadge variant="active">Target Audience</ArtifactBadge>
        <p className="text-foreground mt-1 text-sm font-bold">{audience || 'General'}</p>
      </div>
    </div>
  );
}

function CodeView({ code }: { code: string | null | undefined }) {
  return (
    <div className="group relative">
      <pre className="scrollbar-thin scrollbar-thumb-surface-border scrollbar-track-transparent border-surface-border bg-background text-council-active max-h-[600px] overflow-x-auto rounded-2xl border p-6 font-mono text-xs leading-relaxed dark:opacity-90">
        <code>{code || '# No code generated yet'}</code>
      </pre>
      {code && (
        <button
          onClick={() => navigator.clipboard.writeText(code)}
          className="border-surface-border bg-surface text-tiny text-text-muted hover:text-foreground absolute top-4 right-4 rounded-xl border px-3 py-1.5 font-bold uppercase opacity-0 transition-opacity group-hover:opacity-100"
        >
          Copy Code
        </button>
      )}
    </div>
  );
}

function ThoughtsView({ thoughts }: { thoughts: ThoughtLog[] | undefined }) {
  const groupedThoughts = React.useMemo(() => {
    if (!thoughts || thoughts.length === 0) return [];

    const blocks: { agent: string; phase: string; content: string }[] = [];
    let currentBlock: { agent: string; phase: string; content: string } | null = null;

    thoughts.forEach((t) => {
      if (!currentBlock || currentBlock.agent !== t.agent || currentBlock.phase !== t.phase) {
        currentBlock = { agent: t.agent, phase: t.phase, content: t.content };
        blocks.push(currentBlock);
      } else {
        currentBlock.content += t.content;
      }
    });
    return blocks;
  }, [thoughts]);

  return (
    <div className="scrollbar-thin scrollbar-thumb-surface-border border-surface-border bg-background max-h-[600px] space-y-3 overflow-y-auto rounded-2xl border p-4">
      {groupedThoughts.length === 0 ? (
        <p className="text-text-muted py-8 text-center text-sm italic">No thoughts recorded</p>
      ) : (
        groupedThoughts.map((t) => (
          <div
            key={`${t.agent}:${t.phase}:${t.content.slice(0, 40)}`}
            className="border-council-active/30 border-l-2 py-1 pl-4"
          >
            <div className="mb-1 flex items-center gap-2">
              <span className="bg-council-active/10 text-tiny text-council-active rounded px-2 py-0.5 font-bold tracking-tighter uppercase">
                {t.agent}
              </span>
              <span className="text-tiny text-text-muted font-mono opacity-60">{t.phase}</span>
            </div>
            <p className="text-sm-plus text-text-muted leading-relaxed whitespace-pre-wrap">
              {t.content}
            </p>
          </div>
        ))
      )}
    </div>
  );
}

function TabsSection({
  tabs,
}: {
  tabs: { id: string; label: string; content: React.ReactNode }[];
}) {
  const [activeTab, setActiveTab] = React.useState(tabs[0].id);
  return (
    <div className="flex h-full flex-col">
      <div className="border-surface-border scrollbar-none mb-6 flex gap-1 overflow-x-auto border-b">
        <LazyMotion features={domAnimation}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`-mb-px shrink-0 border-b-2 px-3 py-3 text-[10px] font-bold tracking-widest uppercase transition-all ${
                activeTab === tab.id
                  ? 'border-council-active bg-council-active/5 text-council-active'
                  : 'text-text-muted hover:text-foreground hover:bg-surface-border/10 border-transparent'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </LazyMotion>
      </div>
      <div className="animate-in fade-in slide-in-from-bottom-2 flex-1 duration-300">
        <LazyMotion features={domAnimation}>
          {tabs.find((t) => t.id === activeTab)?.content}
        </LazyMotion>
      </div>
    </div>
  );
}
