import {
  ShieldCheck,
  AlertCircle,
  MessageSquare,
  Layers,
  Clock,
  Check,
  Sparkles,
} from 'lucide-react';
import { ArtifactBadge } from './artifacts/ArtifactCommon';

interface AnalystVerdictProps {
  /** Validation result object from the backend. */
  validation: any;
}

/**
 * Displays the AI analyst's validation verdict including feedback,
 * quality checks, and optimization suggestions.
 */
export function AnalystVerdict({ validation }: AnalystVerdictProps) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {validation.is_valid ? (
            <ShieldCheck className="h-5 w-5 text-success" />
          ) : (
            <AlertCircle className="h-5 w-5 text-warning" />
          )}
          <span
            className={`text-xs font-bold tracking-wider uppercase ${validation.is_valid ? 'text-success' : 'text-warning'}`}
          >
            {validation.is_valid ? 'Council Approved' : 'Needs Refinement'}
          </span>
        </div>
      </div>

      {/* Analyst Feedback Quote */}
      <div className="relative rounded-xl border border-council-active/10 bg-council-active/5 p-4 italic">
        <MessageSquare className="absolute -top-3 -left-3 h-6 w-6 fill-council-active/10 text-council-active/20" />
        <p className="line-clamp-3 text-sm-plus leading-relaxed text-foreground italic">
          "{validation.feedback}"
        </p>
        <div className="mt-4 flex items-center gap-2">
           <ArtifactBadge variant="active">— Analyst A2A</ArtifactBadge>
           <span className="h-1 w-1 rounded-full bg-council-active/20" />
           <ArtifactBadge>Verified Step 4</ArtifactBadge>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="flex items-center justify-between rounded-xl border border-surface-border bg-background p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <Layers className="h-4 w-4 text-council-completed" />
            <span className="text-xs font-bold text-text-muted uppercase tracking-tight">
              Conceptual Accuracy
            </span>
          </div>
          <Check className="h-4 w-4 text-success" />
        </div>
        <div className="flex items-center justify-between rounded-xl border border-surface-border bg-background p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <Clock className="h-4 w-4 text-council-completed" />
            <span className="text-xs font-bold text-text-muted uppercase tracking-tight">Pacing & Flow</span>
          </div>
          <Check className="h-4 w-4 text-success" />
        </div>
      </div>

      {validation.suggestions?.length > 0 && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-council-active" />
            <h4 className="text-tiny font-bold tracking-[0.2em] text-text-muted uppercase">
              Optimization Tips
            </h4>
          </div>
          <ul className="space-y-3">
            {validation.suggestions.map((s: string, i: number) => (
              <li key={i} className="group flex gap-3 text-xs text-text-muted">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-council-active/20 bg-council-active/10 text-tiny font-bold text-council-active">
                  {i + 1}
                </span>
                <span className="pt-0.5 leading-relaxed font-medium">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
