import {
  ShieldCheck,
  AlertCircle,
  MessageSquare,
  Layers,
  Clock,
  Check,
  Sparkles,
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
            <ShieldCheck className="h-5 w-5 text-emerald-500" />
          ) : (
            <AlertCircle className="h-5 w-5 text-amber-500" />
          )}
          <span
            className={`text-xs font-bold tracking-wider uppercase ${validation.is_valid ? 'text-emerald-500' : 'text-amber-500'}`}
          >
            {validation.is_valid ? 'Council Approved' : 'Needs Refinement'}
          </span>
        </div>
      </div>

      <div className="relative rounded-xl border border-indigo-500/10 bg-indigo-500/5 p-4 italic">
        <MessageSquare className="absolute -top-3 -left-3 h-6 w-6 fill-indigo-500/10 text-indigo-500/20" />
        <p className="line-clamp-3 text-sm leading-relaxed text-[var(--foreground)] italic">
          "{validation.feedback}"
        </p>
        <div className="mt-3 flex items-center gap-2 text-[10px] font-medium tracking-widest text-indigo-500/60 uppercase">
          <span>— Analyst A2A</span>
          <span className="h-1 w-1 rounded-full bg-indigo-500/20" />
          <span>Verified Step 4</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3">
        <div className="flex items-center justify-between rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-3">
          <div className="flex items-center gap-3">
            <Layers className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-medium text-[var(--text-muted)]">
              Conceptual Accuracy
            </span>
          </div>
          <Check className="h-4 w-4 text-emerald-500" />
        </div>
        <div className="flex items-center justify-between rounded-lg border border-[var(--surface-border)] bg-[var(--background)] p-3">
          <div className="flex items-center gap-3">
            <Clock className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-medium text-[var(--text-muted)]">Pacing & Flow</span>
          </div>
          <Check className="h-4 w-4 text-emerald-500" />
        </div>
      </div>

      {validation.suggestions?.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="flex items-center gap-2 text-[10px] font-bold tracking-widest text-indigo-400 uppercase">
            <Sparkles className="h-3 w-3" />
            Optimization Tips
          </h4>
          <ul className="space-y-2">
            {validation.suggestions.map((s: string, i: number) => (
              <li key={i} className="group flex gap-3 text-xs text-[var(--text-muted)]">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-indigo-500/20 bg-indigo-500/10 text-[10px] text-indigo-500">
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
