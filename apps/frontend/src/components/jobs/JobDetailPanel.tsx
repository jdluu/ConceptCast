import React from 'react';
import { JobStatus, ThoughtLog } from '@/lib/api/client';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { VideoPlayer } from '@/components/ui/VideoPlayer';
import { format } from 'date-fns';
import { formatDuration } from '@/lib/utils/durationUtils';

interface JobDetailPanelProps {
    job: JobStatus;
}

export function JobDetailPanel({ job }: JobDetailPanelProps) {
    const topic = job.topic || 'Unknown Topic';
    const audience = job.target_audience || 'General';

    return (
        <div className="p-8 bg-[var(--surface)] border-t border-[var(--surface-border)] animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column: Preview & Metadata */}
                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider">Video Preview</h3>
                        <StatusBadge status={job.status} />
                    </div>
                    {job.video_url ? (
                        <div className="rounded-xl overflow-hidden border border-[var(--surface-border)] shadow-2xl shadow-indigo-500/10">
                            <VideoPlayer src={job.video_url} />
                        </div>
                    ) : (
                        <div className="aspect-video bg-[var(--background)]/50 rounded-xl flex items-center justify-center border border-dashed border-[var(--surface-border)]">
                            <span className="text-[var(--text-muted)] text-sm">Video not yet rendered</span>
                        </div>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                        <DataCard label="Model" value={job.model_id || 'Unknown'} subValue={job.provider || ''} />
                        <DataCard label="Cost" value={`$${(job as any).cost?.toFixed(2) || '0.00'}`} />
                        <DataCard label="Created" value={job.started_at ? format(new Date(job.started_at), 'PPPp') : 'Pending'} />
                        <DataCard label="Duration" value={formatDuration(job.duration_seconds)} />
                    </div>
                </div>

                {/* Right Column: Prompt & Code */}
                <div className="space-y-6">
                    <TabsSection tabs={[
                        { id: 'prompt', label: 'Prompt', content: <PromptView topic={topic} audience={audience} /> },
                        { id: 'code', label: 'Manim Code', content: <CodeView code={job.manim_code} /> },
                        { id: 'thoughts', label: 'Thought Log', content: <ThoughtsView thoughts={job.streamed_thoughts} /> }
                    ]} />
                </div>
            </div>

            {job.error && (
                <div className="mt-8 p-4 bg-red-950/20 border border-red-900/50 rounded-lg">
                    <h4 className="text-red-400 text-xs font-bold uppercase mb-1">Execution Error</h4>
                    <p className="text-red-300 text-sm font-mono whitespace-pre-wrap">{job.error}</p>
                </div>
            )}
        </div>
    );
}

function DataCard({ label, value, subValue }: { label: string; value: string; subValue?: string }) {
    return (
        <div className="p-4 bg-[var(--background)]/30 rounded-lg border border-[var(--surface-border)]">
            <span className="block text-[10px] text-[var(--text-muted)] uppercase font-bold tracking-tight mb-1">{label}</span>
            <span className="block text-sm text-[var(--foreground)] font-bold truncate" title={value}>{value}</span>
            {subValue && <span className="block text-[10px] text-[var(--text-muted)] opacity-60 truncate">{subValue}</span>}
        </div>
    );
}

function PromptView({ topic, audience }: { topic: string; audience: string | null | undefined }) {
    return (
        <div className="bg-[var(--background)]/30 p-4 rounded-lg border border-[var(--surface-border)] min-h-[200px]">
            <div className="mb-4">
                <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Topic</span>
                <p className="text-sm text-[var(--foreground)] font-medium mt-1">{topic}</p>
            </div>
            <div>
                <span className="text-[10px] text-[var(--text-muted)] uppercase font-bold">Target Audience</span>
                <p className="text-sm text-[var(--foreground)] font-medium mt-1">{audience || 'General'}</p>
            </div>
        </div>
    );
}

function CodeView({ code }: { code: string | null | undefined }) {
    return (
        <div className="relative group">
            <pre className="p-4 bg-[var(--background)] rounded-lg border border-[var(--surface-border)] overflow-x-auto max-h-[400px] text-[12px] leading-relaxed font-mono text-indigo-400 dark:text-indigo-300/90 scrollbar-thin scrollbar-thumb-[var(--surface-border)] scrollbar-track-transparent">
                <code>{code || '# No code generated yet'}</code>
            </pre>
                {code && (
                <button 
                    onClick={() => navigator.clipboard.writeText(code)}
                    className="absolute top-2 right-2 p-2 bg-[var(--surface)] border border-[var(--surface-border)] rounded-md text-[var(--text-muted)] opacity-0 group-hover:opacity-100 transition-opacity hover:text-[var(--foreground)]"
                >
                    Copy
                </button>
            )}
        </div>
    );
}

function ThoughtsView({ thoughts }: { thoughts: ThoughtLog[] | undefined }) {
    return (
        <div className="bg-[var(--background)] p-4 rounded-lg border border-[var(--surface-border)] max-h-[400px] overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-[var(--surface-border)]">
            {(!thoughts || thoughts.length === 0) ? (
                <p className="text-[var(--text-muted)] text-sm italic py-4 text-center">No thoughts recorded</p>
            ) : (
                thoughts.map((t, i) => (
                    <div key={i} className="border-l-2 border-indigo-500/30 pl-3 py-0.5">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-[10px] bg-indigo-500/10 text-indigo-500 px-1.5 py-0.5 rounded uppercase font-bold tracking-tighter">{t.agent}</span>
                            <span className="text-[10px] text-[var(--text-muted)] opacity-60 font-mono">{t.phase}</span>
                        </div>
                        <p className="text-sm text-[var(--text-muted)] leading-snug">{t.content}</p>
                    </div>
                ))
            )}
        </div>
    );
}

function TabsSection({ tabs }: { tabs: { id: string; label: string; content: React.ReactNode }[] }) {
    const [activeTab, setActiveTab] = React.useState(tabs[0].id);
    return (
        <div>
            <div className="flex border-b border-[var(--surface-border)] mb-4">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors border-b-2 -mb-px ${
                            activeTab === tab.id 
                            ? 'text-indigo-500 border-indigo-500 bg-indigo-500/5' 
                            : 'text-[var(--text-muted)] border-transparent hover:text-[var(--foreground)]'
                        }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>
            {tabs.find(t => t.id === activeTab)?.content}
        </div>
    );
}
