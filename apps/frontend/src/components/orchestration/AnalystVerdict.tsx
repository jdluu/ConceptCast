import { 
    ShieldCheck, 
    AlertCircle, 
    MessageSquare, 
    Layers,
    Clock,
    Check,
    Sparkles
} from 'lucide-react';

interface AnalystVerdictProps {
    /** Validation result object from the backend. */
    validation: any;
}

/**
 * Displays the AI analyst's validation verdict including feedback,
 * quality checks, and optimization suggestions.
 *
 * @param {AnalystVerdictProps} props - Component properties.
 * @returns {JSX.Element} The rendered verdict panel.
 */
export function AnalystVerdict({ validation }: AnalystVerdictProps) {
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
