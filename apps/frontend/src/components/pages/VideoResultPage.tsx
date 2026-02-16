import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    ShieldCheck, 
    AlertCircle, 
    MessageSquare, 
    Lightbulb, 
    Video, 
    Code, 
    Copy, 
    Check, 
    Clock,
    Layers,
    Type,
    Sparkles,
    ChevronDown,
    PlayCircle
} from 'lucide-react';
import type { CurriculumPlan, Storyboard } from '../../lib/api/client';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { formatDuration, formatGenerationTime } from '../../lib/utils/duration-utils';

interface VideoResultPageProps {
    videoUrl: string | null;
    conceptTitle: string;
    plan: CurriculumPlan;
    storyboard: Storyboard;
    validation?: any;
    manimCode?: string | null;
    durationSeconds?: number | null;
    videoMetadata?: any | null;
    onReset: () => void;
}

function CollapsiblePanel({
    title,
    icon: Icon,
    children,
    defaultOpen = true,
}: {
    title: string;
    icon?: any;
    children: React.ReactNode;
    defaultOpen?: boolean;
}) {
    const [open, setOpen] = useState(defaultOpen);

    return (
        <Card className="overflow-hidden border-[var(--surface-border)] shadow-sm bg-[var(--surface)] transition-all duration-300">
            <button
                type="button"
                onClick={() => setOpen((o) => !o)}
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-[var(--background)]/50 transition-colors group"
                aria-expanded={open}
            >
                <div className="flex items-center gap-3">
                    {Icon && <Icon className="w-4 h-4 text-indigo-500" />}
                    <span className="font-bold text-[var(--foreground)] uppercase tracking-wider text-xs">
                        {title}
                    </span>
                </div>
                <ChevronDown
                    className={`w-4 h-4 text-[var(--text-muted)] transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
                    aria-hidden
                />
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: 'easeInOut' }}
                    >
                        <div className="px-6 pb-6 pt-0">{children}</div>
                    </motion.div>
                )}
            </AnimatePresence>
        </Card>
    );
}

function AnalystVerdict({ validation }: { validation: any }) {
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {validation.is_valid ? (
                        <ShieldCheck className="w-5 h-5 text-emerald-500" />
                    ) : (
                        <AlertCircle className="w-5 h-5 text-amber-500" />
                    )}
                    <span className={`text-xs font-bold uppercase tracking-wider ${validation.is_valid ? 'text-emerald-500' : 'text-amber-500'}`}>
                        {validation.is_valid ? 'Council Approved' : 'Needs Refinement'}
                    </span>
                </div>
            </div>

            <div className="relative p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 italic">
                <MessageSquare className="absolute -top-3 -left-3 w-6 h-6 text-indigo-500/20 fill-indigo-500/10" />
                <p className="text-sm text-[var(--foreground)] leading-relaxed italic line-clamp-3">
                    "{validation.feedback}"
                </p>
                <div className="mt-3 flex items-center gap-2 text-[10px] text-indigo-500/60 font-medium uppercase tracking-widest">
                    <span>— Analyst A2A</span>
                    <span className="w-1 h-1 rounded-full bg-indigo-500/20" />
                    <span>Verified Step 4</span>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-3">
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--background)] border border-[var(--surface-border)]">
                    <div className="flex items-center gap-3">
                        <Layers className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs text-[var(--text-muted)] font-medium">Conceptual Accuracy</span>
                    </div>
                    <Check className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--background)] border border-[var(--surface-border)]">
                    <div className="flex items-center gap-3">
                        <Clock className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs text-[var(--text-muted)] font-medium">Pacing & Flow</span>
                    </div>
                    <Check className="w-4 h-4 text-emerald-500" />
                </div>
            </div>

            {validation.suggestions?.length > 0 && (
                <div className="space-y-3 pt-2">
                    <h4 className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-2">
                        <Sparkles className="w-3 h-3" />
                        Optimization Tips
                    </h4>
                    <ul className="space-y-2">
                        {validation.suggestions.map((s: string, i: number) => (
                            <li key={i} className="text-xs text-[var(--text-muted)] flex gap-3 group">
                                <span className="w-5 h-5 rounded-full bg-indigo-500/10 flex items-center justify-center text-[10px] text-indigo-500 shrink-0 border border-indigo-500/20">
                                    {i + 1}
                                </span>
                                <span className="pt-0.5 leading-relaxed">{s}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

function CurriculumTimeline({ plan }: { plan: CurriculumPlan }) {
    return (
        <div className="relative pl-6 space-y-8 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-px before:bg-gradient-to-b before:from-indigo-500/50 before:via-indigo-500/20 before:to-transparent before:border-l before:border-dashed before:border-indigo-500/30">
            {plan.teaching_steps.map((step) => (
                <motion.div 
                    key={step.step_id}
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className="relative"
                >
                    <div className="absolute -left-[31px] top-1 w-6 h-6 rounded-lg bg-indigo-600 border-2 border-[var(--surface)] text-white flex items-center justify-center text-[10px] font-bold shadow-md shadow-indigo-600/20 z-10">
                        {step.step_id}
                    </div>
                    <div className="p-4 rounded-xl bg-[var(--background)] border border-[var(--surface-border)] hover:border-indigo-500/30 transition-all group/step shadow-sm">
                        <div className="flex items-start justify-between gap-4 mb-2">
                            <h3 className="font-bold text-sm text-[var(--foreground)] group-hover/step:text-indigo-600 dark:group-hover/step:text-indigo-400 transition-colors">
                                {step.concept}
                            </h3>
                            <Lightbulb className="w-4 h-4 text-amber-400/50 group-hover/step:text-amber-400 transition-colors shrink-0" />
                        </div>
                        <p className="text-xs text-[var(--text-muted)] leading-relaxed italic opacity-80 border-l-2 border-indigo-500/10 pl-3">
                            {step.visual_metaphor}
                        </p>
                    </div>
                </motion.div>
            ))}
        </div>
    );
}

function SceneGallery({ storyboard }: { storyboard: Storyboard }) {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {storyboard.scenes.map((scene) => (
                <motion.div 
                    key={scene.scene_id}
                    whileHover={{ scale: 1.01 }}
                    className="flex flex-col rounded-xl bg-[var(--background)] border border-[var(--surface-border)] overflow-hidden hover:border-indigo-500/30 transition-all shadow-sm group/scene"
                >
                    {/* Mock Scene Thumbnail */}
                    <div className="aspect-video bg-[var(--surface)] flex items-center justify-center relative border-b border-[var(--surface-border)]">
                        <Video className="w-8 h-8 text-indigo-500/20 group-hover/scene:scale-110 group-hover/scene:text-indigo-500/40 transition-all duration-500" />
                        <div className="absolute top-3 left-3 px-2 py-0.5 rounded bg-black/50 text-[9px] font-bold text-white uppercase tracking-widest backdrop-blur-sm">
                            Scene {scene.scene_id}
                        </div>
                    </div>
                    
                    <div className="p-4 space-y-3">
                        <h4 className="text-xs font-bold text-[var(--foreground)] uppercase group-hover/scene:text-indigo-500 transition-colors">
                            {scene.title}
                        </h4>
                        
                        <div className="space-y-2">
                            <div className="flex gap-2">
                                <Layers className="w-3 h-3 text-indigo-500 shrink-0 mt-0.5" />
                                <p className="text-[11px] text-[var(--text-muted)] line-clamp-2 leading-relaxed">
                                    {scene.description}
                                </p>
                            </div>
                            {scene.narration && (
                                <div className="flex gap-2 p-2 rounded bg-indigo-500/[0.03] border border-indigo-500/5">
                                    <Type className="w-3 h-3 text-indigo-400/60 shrink-0 mt-0.5" />
                                    <p className="text-[10px] text-[var(--text-muted)] italic line-clamp-2 opacity-70">
                                        "{scene.narration}"
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </motion.div>
            ))}
        </div>
    );
}

function CodeWorkspace({ code }: { code: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative rounded-xl overflow-hidden border border-[var(--surface-border)] bg-[#1e1e1e] group/code">
            <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-red-500/50" />
                        <div className="w-2 h-2 rounded-full bg-amber-500/50" />
                        <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
                    </div>
                    <span className="text-[10px] font-mono text-white/40 ml-2 uppercase tracking-widest">manim_scene.py</span>
                </div>
                <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleCopy}
                    className="h-7 px-2 text-white/40 hover:text-white hover:bg-white/10"
                >
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span className="text-[10px] font-bold uppercase ml-1">{copied ? 'Copied' : 'Copy'}</span>
                </Button>
            </div>
            
            <div className="p-4 overflow-x-auto max-h-[400px] custom-scrollbar">
                <pre className="text-[11px] font-mono leading-relaxed">
                    <code>
                        {code.split('\n').map((line, i) => (
                            <div key={i} className="flex gap-4 opacity-80 hover:opacity-100 transition-opacity">
                                <span className="w-6 shrink-0 text-right text-white/20 select-none">{i + 1}</span>
                                <span className="text-blue-300">
                                    {line.replace(/class|def|from|import/g, (m) => `\x00${m}\x00`)
                                         .split('\x00').map((part, pi) => (
                                             pi % 2 === 1 ? <span key={pi} className="text-purple-400">{part}</span> : part
                                         ))}
                                </span>
                            </div>
                        ))}
                    </code>
                </pre>
            </div>
        </div>
    );
}

export function VideoResultPage({ 
    videoUrl, 
    conceptTitle, 
    plan, 
    storyboard, 
    validation,
    manimCode,
    durationSeconds,
    videoMetadata,
    onReset 
}: VideoResultPageProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (videoUrl && videoRef.current) videoRef.current.load();
    }, [videoUrl]);

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header with Back Button */}
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-[var(--foreground)] tracking-tight">{conceptTitle}</h1>
                <button
                    onClick={onReset}
                    className="h-11 px-6 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/20 active:scale-95"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
                    </svg>
                    Create New Video
                </button>
            </div>

            {/* Video metadata overview */}
            <div className="flex flex-wrap gap-4 items-center px-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20">
                    <Clock className="w-3.5 h-3.5 text-indigo-500" />
                    <span className="text-[11px] font-bold text-indigo-500 uppercase tracking-widest leading-none">
                        Gen Time: {formatGenerationTime(durationSeconds)}
                    </span>
                </div>
                {videoMetadata?.duration && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                        <PlayCircle className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="text-[11px] font-bold text-emerald-500 uppercase tracking-widest leading-none">
                            Duration: {formatDuration(Number(videoMetadata.duration))}
                        </span>
                    </div>
                )}
                {videoMetadata?.resolution && (
                    <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-widest px-1">
                        {videoMetadata.resolution} • {videoMetadata.file_size || 'N/A'}
                    </div>
                )}
            </div>

            {/* Video player or placeholder at top */}
            <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-3xl overflow-hidden shadow-2xl transition-all">
                <div className="relative aspect-video bg-black shadow-inner">
                    {videoUrl ? (
                        <video
                            ref={videoRef}
                            className="w-full h-full object-contain"
                            controls
                            autoPlay
                            playsInline
                        >
                            <source src={videoUrl} type="video/mp4" />
                            Your browser does not support the video tag.
                        </video>
                    ) : (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="text-center px-6">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-16 h-16 mx-auto mb-4 text-[var(--text-muted)] opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <p className="text-lg font-bold text-[var(--text-muted)] opacity-60">Video not available</p>
                                <p className="text-sm text-[var(--text-muted)] opacity-40 mt-2 max-w-xs mx-auto">Mock runs skip rendering. Use a live provider to generate a video.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Artifact Panels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-20">
                {/* 1. Validation / Critique */}
                {validation && (
                    <CollapsiblePanel title="Council Verdict" icon={ShieldCheck}>
                        <AnalystVerdict validation={validation} />
                    </CollapsiblePanel>
                )}

                {/* 2. Curriculum Plan */}
                <CollapsiblePanel title="Curriculum Timeline" icon={Lightbulb}>
                    <CurriculumTimeline plan={plan} />
                </CollapsiblePanel>

                {/* 3. Visual Storyboard */}
                <CollapsiblePanel title="Visual Storyboard" icon={Video}>
                    <SceneGallery storyboard={storyboard} />
                </CollapsiblePanel>

                {/* 4. Technical Script */}
                {manimCode && (
                    <CollapsiblePanel title="Technical Script" icon={Code} defaultOpen={false}>
                        <CodeWorkspace code={manimCode} />
                    </CollapsiblePanel>
                )}
            </div>
        </div>
    );
}
