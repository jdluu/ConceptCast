import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { getJobStatus, JobStatus, ThoughtLog, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { CurriculumTimeline } from '@/components/orchestration/CurriculumTimeline';
import { ArtifactCard, ArtifactBadge } from '@/components/orchestration/artifacts/ArtifactCommon';
import { AnalystVerdict } from '@/components/orchestration/AnalystVerdict';
import { format } from 'date-fns';
import { formatDuration } from '@/lib/utils/durationUtils';
import { isJobInProgress } from '@/lib/utils/jobUtils';
import { Loader2 } from 'lucide-react';

interface JobDetailPanelProps {
  jobId: string;
  initialData?: JobStatus;
}

/**
 * Detailed view of a job's artifacts and metadata.
 * Self-updates when the job is in progress.
 */
export function JobDetailPanel({ jobId, initialData }: JobDetailPanelProps) {
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId),
    initialData,
    refetchInterval: (query) => 
      query.state.data && isJobInProgress(query.state.data) ? 3000 : false,
  });

  if (isLoading || !job) {
    return (
      <div className="flex flex-col items-center justify-center bg-surface/50 p-12 text-center">
        <Loader2 className="mb-2 h-6 w-6 animate-spin text-council-active" />
        <span className="text-sm text-text-muted">Fetching job details...</span>
      </div>
    );
  }

  const topic = job.topic || 'Unknown Topic';
  const audience = job.target_audience || 'General';

  return (
    <div className="animate-in fade-in slide-in-from-top-4 border-t border-surface-border bg-surface p-8 duration-300">
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left Column: Preview & Metadata */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold tracking-[0.2em] text-text-muted uppercase">
              Video Preview
            </h3>
            <div className="flex items-center gap-2">
              {job.status === 'rendering' && (
                <div className="flex items-center gap-2 mr-2">
                  <div className="h-1.5 w-24 overflow-hidden rounded-full bg-surface-border">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${job.render_progress}%` }}
                      className="h-full bg-council-active" 
                    />
                  </div>
                  <span className="font-mono text-[10px] font-bold text-council-active">
                    {Math.round(job.render_progress)}%
                  </span>
                </div>
              )}
              <span className={`rounded-md px-2 py-0.5 text-nano font-bold uppercase tracking-widest ${job.mode === 'mock' ? 'bg-warning/10 text-warning' : 'bg-info/10 text-info'}`}>
                {job.mode}
              </span>
              <StatusBadge status={job.status} />
            </div>
          </div>
          {job.video_url ? (
            <div className="overflow-hidden rounded-2xl border border-surface-border shadow-2xl shadow-council-active/10">
              <VideoPlayer src={job.video_url} />
            </div>
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-2xl border border-dashed border-surface-border bg-background/50">
              <span className="text-sm text-text-muted italic">Video not yet rendered</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <DataCard
              label="Model"
              value={job.model_id || 'Unknown'}
              subValue={job.provider || ''}
            />
            <DataCard
              label="Format"
              value={job.resolution || 'N/A'}
              subValue={`${job.frame_rate} FPS`}
            />
            <DataCard
              label="Timeline"
              value={job.started_at ? format(new Date(job.started_at), 'PPP') : 'Pending'}
              subValue={
                job.status !== 'completed' && job.status !== 'failed' && job.current_step
                  ? `Active: ${job.current_step}`
                  : job.started_at ? format(new Date(job.started_at), 'p') : ''
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
        <div className="space-y-6">
          <TabsSection
            tabs={[
              {
                id: 'prompt',
                label: 'Prompt',
                content: <PromptView topic={topic} audience={audience} />,
              },
              {
                id: 'plan',
                label: 'Pedagogy',
                content: job.plan ? (
                  <CurriculumTimeline plan={job.plan as unknown as CurriculumPlan} />
                ) : (
                  <NoArtifact title="Curriculum Plan" />
                ),
              },
              {
                id: 'validation',
                label: 'Verdict',
                content: job.validation ? (
                  <AnalystVerdict validation={job.validation} />
                ) : (
                  <NoArtifact title="Pedagogical Validation" />
                ),
              },
              {
                id: 'storyboard',
                label: 'Visuals',
                content: job.storyboard ? (
                  <StoryboardView storyboard={job.storyboard as unknown as Storyboard} />
                ) : (
                  <NoArtifact title="Storyboard" />
                ),
              },
              { id: 'code', label: 'Script', content: <CodeView code={job.manim_code} /> },
              {
                id: 'thoughts',
                label: 'Log',
                content: <ThoughtsView thoughts={job.streamed_thoughts} />,
              },
            ]}
          />
        </div>
      </div>

      {job.error && (
        <div className="mt-8 rounded-xl border border-destructive/20 bg-destructive/5 p-4 shadow-sm shadow-destructive/10">
          <h4 className="mb-1 text-xs font-bold text-destructive uppercase tracking-widest">Execution Error</h4>
          <p className="font-mono text-sm whitespace-pre-wrap text-destructive dark:text-destructive">{job.error}</p>
        </div>
      )}
    </div>
  );
}

function NoArtifact({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-surface-border bg-background/30 p-12 text-center">
      <p className="text-sm text-text-muted italic">{title} not available yet</p>
    </div>
  );
}

function StoryboardView({ storyboard }: { storyboard: Storyboard }) {
  return (
    <div className="scrollbar-thin scrollbar-thumb-surface-border max-h-md space-y-4 overflow-y-auto pr-2">
      {storyboard.scenes.map((scene) => (
        <ArtifactCard
          key={scene.scene_id}
          className="hover:border-council-active/30"
        >
          <ArtifactBadge>SCENE {scene.scene_id}</ArtifactBadge>
          <h4 className="mb-2 text-sm-plus font-bold tracking-tight text-foreground uppercase">
            {scene.title}
          </h4>
          <p className="text-xs leading-relaxed text-text-muted">{scene.description}</p>
          {scene.objects && (
            <div className="mt-3 border-t border-surface-border/50 pt-2">
              <ArtifactBadge variant="active">Visual Elements</ArtifactBadge>
              <div className="mt-1 flex flex-wrap gap-1.5">
                {scene.objects.map((v, i) => (
                  <span
                    key={i}
                    className="rounded-md border border-council-active/10 bg-council-active/5 px-2 py-0.5 text-tiny font-medium text-council-active"
                  >
                    {v.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </ArtifactCard>
      ))}
    </div>
  );
}

function DataCard({ label, value, subValue }: { label: string; value: string; subValue?: string }) {
  return (
    <div className="rounded-xl border border-surface-border bg-background/30 p-4 shadow-sm">
      <ArtifactBadge>{label}</ArtifactBadge>
      <span className="block truncate text-sm font-bold text-foreground" title={value}>
        {value}
      </span>
      {subValue && (
        <span className="block truncate text-tiny text-text-muted opacity-60">
          {subValue}
        </span>
      )}
    </div>
  );
}

function PromptView({ topic, audience }: { topic: string; audience: string | null | undefined }) {
  return (
    <div className="min-h-xs rounded-2xl border border-surface-border bg-background/30 p-6 space-y-6">
      <div>
        <ArtifactBadge variant="active">Topic</ArtifactBadge>
        <p className="mt-1 text-sm font-bold text-foreground">{topic}</p>
      </div>
      <div>
        <ArtifactBadge variant="active">
          Target Audience
        </ArtifactBadge>
        <p className="mt-1 text-sm font-bold text-foreground">{audience || 'General'}</p>
      </div>
    </div>
  );
}

function CodeView({ code }: { code: string | null | undefined }) {
  return (
    <div className="group relative">
      <pre className="scrollbar-thin scrollbar-thumb-surface-border scrollbar-track-transparent max-h-md overflow-x-auto rounded-2xl border border-surface-border bg-background p-6 font-mono text-xs leading-relaxed text-council-active dark:opacity-90">
        <code>{code || '# No code generated yet'}</code>
      </pre>
      {code && (
        <button
          onClick={() => navigator.clipboard.writeText(code)}
          className="absolute top-4 right-4 rounded-xl border border-surface-border bg-surface px-3 py-1.5 text-tiny font-bold uppercase text-text-muted opacity-0 transition-opacity group-hover:opacity-100 hover:text-foreground"
        >
          Copy Code
        </button>
      )}
    </div>
  );
}

function ThoughtsView({ thoughts }: { thoughts: ThoughtLog[] | undefined }) {
  return (
    <div className="scrollbar-thin scrollbar-thumb-surface-border max-h-md space-y-3 overflow-y-auto rounded-2xl border border-surface-border bg-background p-4">
      {!thoughts || thoughts.length === 0 ? (
        <p className="py-8 text-center text-sm text-text-muted italic">
          No thoughts recorded
        </p>
      ) : (
        thoughts.map((t, i) => (
          <div key={i} className="border-l-2 border-council-active/30 py-1 pl-4">
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded bg-council-active/10 px-2 py-0.5 text-tiny font-bold tracking-tighter text-council-active uppercase">
                {t.agent}
              </span>
              <span className="font-mono text-tiny text-text-muted opacity-60">
                {t.phase}
              </span>
            </div>
            <p className="text-sm-plus leading-snug text-text-muted">{t.content}</p>
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
    <div>
      <div className="mb-6 flex overflow-x-auto border-b border-surface-border scrollbar-none">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`-mb-px shrink-0 border-b-2 px-4 py-3 text-tiny font-bold tracking-[0.2em] uppercase transition-all ${
              activeTab === tab.id
                ? 'border-council-active bg-council-active/5 text-council-active'
                : 'border-transparent text-text-muted hover:text-foreground hover:bg-surface-border/20'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
        {tabs.find((t) => t.id === activeTab)?.content}
      </div>
    </div>
  );
}
