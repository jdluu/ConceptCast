import React from 'react';
import { JobStatus, ThoughtLog, CurriculumPlan, Storyboard } from '@/lib/api/client';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { CurriculumTimeline } from '@/components/orchestration/CurriculumTimeline';
import { format } from 'date-fns';
import { formatDuration } from '@/lib/utils/durationUtils';

interface JobDetailPanelProps {
  job: JobStatus;
}

export function JobDetailPanel({ job }: JobDetailPanelProps) {
  const topic = job.topic || 'Unknown Topic';
  const audience = job.target_audience || 'General';

  return (
    <div className="animate-in fade-in slide-in-from-top-4 border-t border-[var(--surface-border)] bg-[var(--surface)] p-8 duration-300">
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left Column: Preview & Metadata */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold tracking-wider text-[var(--text-muted)] uppercase">
              Video Preview
            </h3>
            <StatusBadge status={job.status} />
          </div>
          {job.video_url ? (
            <div className="overflow-hidden rounded-xl border border-[var(--surface-border)] shadow-2xl shadow-indigo-500/10">
              <VideoPlayer src={job.video_url} />
            </div>
          ) : (
            <div className="flex aspect-video items-center justify-center rounded-xl border border-dashed border-[var(--surface-border)] bg-[var(--background)]/50">
              <span className="text-sm text-[var(--text-muted)]">Video not yet rendered</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <DataCard
              label="Model"
              value={job.model_id || 'Unknown'}
              subValue={job.provider || ''}
            />
            <DataCard
              label="Created"
              value={job.started_at ? format(new Date(job.started_at), 'PPPp') : 'Pending'}
            />
            <DataCard label="Duration" value={formatDuration(job.duration_seconds)} />
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
                label: 'Planned Curriculum',
                content: job.plan ? (
                  <CurriculumTimeline plan={job.plan as unknown as CurriculumPlan} />
                ) : (
                  <NoArtifact title="Curriculum Plan" />
                ),
              },
              {
                id: 'storyboard',
                label: 'Visual Storyboard',
                content: job.storyboard ? (
                  <StoryboardView storyboard={job.storyboard as unknown as Storyboard} />
                ) : (
                  <NoArtifact title="Storyboard" />
                ),
              },
              { id: 'code', label: 'Manim Code', content: <CodeView code={job.manim_code} /> },
              {
                id: 'thoughts',
                label: 'Thought Log',
                content: <ThoughtsView thoughts={job.streamed_thoughts} />,
              },
            ]}
          />
        </div>
      </div>

      {job.error && (
        <div className="mt-8 rounded-lg border border-red-900/50 bg-red-950/20 p-4">
          <h4 className="mb-1 text-xs font-bold text-red-400 uppercase">Execution Error</h4>
          <p className="font-mono text-sm whitespace-pre-wrap text-red-300">{job.error}</p>
        </div>
      )}
    </div>
  );
}

function NoArtifact({ title }: { title: string }) {
  return (
    <div className="rounded-lg border border-dashed border-[var(--surface-border)] bg-[var(--background)]/30 p-12 text-center">
      <p className="text-sm text-[var(--text-muted)] italic">{title} not available yet</p>
    </div>
  );
}

function StoryboardView({ storyboard }: { storyboard: Storyboard }) {
  return (
    <div className="scrollbar-thin scrollbar-thumb-[var(--surface-border)] max-h-[400px] space-y-4 overflow-y-auto pr-2">
      {storyboard.scenes.map((scene) => (
        <div
          key={scene.scene_id}
          className="rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-4 shadow-sm transition-all hover:border-indigo-500/30"
        >
          <div className="mb-1 text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">
            SCENE {scene.scene_id}
          </div>
          <h4 className="mb-2 text-sm font-bold tracking-tight text-[var(--foreground)] uppercase">
            {scene.title}
          </h4>
          <p className="text-xs leading-relaxed text-[var(--text-muted)]">{scene.description}</p>
          {scene.objects && (
            <div className="mt-2 border-t border-[var(--surface-border)]/50 pt-2">
              <span className="text-[9px] font-bold tracking-tighter text-indigo-500 uppercase">
                Visual Elements
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {scene.objects.map((v, i) => (
                  <span
                    key={i}
                    className="rounded border border-indigo-500/10 bg-indigo-500/5 px-1.5 py-0.5 text-[9px] text-indigo-400"
                  >
                    {v.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function DataCard({ label, value, subValue }: { label: string; value: string; subValue?: string }) {
  return (
    <div className="rounded-lg border border-[var(--surface-border)] bg-[var(--background)]/30 p-4">
      <span className="mb-1 block text-[10px] font-bold tracking-tight text-[var(--text-muted)] uppercase">
        {label}
      </span>
      <span className="block truncate text-sm font-bold text-[var(--foreground)]" title={value}>
        {value}
      </span>
      {subValue && (
        <span className="block truncate text-[10px] text-[var(--text-muted)] opacity-60">
          {subValue}
        </span>
      )}
    </div>
  );
}

function PromptView({ topic, audience }: { topic: string; audience: string | null | undefined }) {
  return (
    <div className="min-h-[200px] rounded-lg border border-[var(--surface-border)] bg-[var(--background)]/30 p-4">
      <div className="mb-4">
        <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Topic</span>
        <p className="mt-1 text-sm font-medium text-[var(--foreground)]">{topic}</p>
      </div>
      <div>
        <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">
          Target Audience
        </span>
        <p className="mt-1 text-sm font-medium text-[var(--foreground)]">{audience || 'General'}</p>
      </div>
    </div>
  );
}

function CodeView({ code }: { code: string | null | undefined }) {
  return (
    <div className="group relative">
      <pre className="scrollbar-thin scrollbar-thumb-[var(--surface-border)] scrollbar-track-transparent max-h-[400px] overflow-x-auto rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-4 font-mono text-[12px] leading-relaxed text-indigo-400 dark:text-indigo-300/90">
        <code>{code || '# No code generated yet'}</code>
      </pre>
      {code && (
        <button
          onClick={() => navigator.clipboard.writeText(code)}
          className="absolute top-2 right-2 rounded-md border border-[var(--surface-border)] bg-[var(--surface)] p-2 text-[var(--text-muted)] opacity-0 transition-opacity group-hover:opacity-100 hover:text-[var(--foreground)]"
        >
          Copy
        </button>
      )}
    </div>
  );
}

function ThoughtsView({ thoughts }: { thoughts: ThoughtLog[] | undefined }) {
  return (
    <div className="scrollbar-thin scrollbar-thumb-[var(--surface-border)] max-h-[400px] space-y-3 overflow-y-auto rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-4">
      {!thoughts || thoughts.length === 0 ? (
        <p className="py-4 text-center text-sm text-[var(--text-muted)] italic">
          No thoughts recorded
        </p>
      ) : (
        thoughts.map((t, i) => (
          <div key={i} className="border-l-2 border-indigo-500/30 py-0.5 pl-3">
            <div className="mb-1 flex items-center gap-2">
              <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-bold tracking-tighter text-indigo-500 uppercase">
                {t.agent}
              </span>
              <span className="font-mono text-[10px] text-[var(--text-muted)] opacity-60">
                {t.phase}
              </span>
            </div>
            <p className="text-sm leading-snug text-[var(--text-muted)]">{t.content}</p>
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
      <div className="mb-4 flex border-b border-[var(--surface-border)]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`-mb-px border-b-2 px-4 py-2 text-xs font-bold tracking-wider uppercase transition-colors ${
              activeTab === tab.id
                ? 'border-indigo-500 bg-indigo-500/5 text-indigo-500'
                : 'border-transparent text-[var(--text-muted)] hover:text-[var(--foreground)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.find((t) => t.id === activeTab)?.content}
    </div>
  );
}
