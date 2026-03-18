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
            <ShieldCheck className="text-success h-5 w-5" />
          ) : (
            <AlertCircle className="text-warning h-5 w-5" />
          )}
          <span
            className={`text-xs font-bold tracking-wider uppercase ${validation.is_valid ? 'text-success' : 'text-warning'}`}
          >
            {validation.is_valid ? 'Council Approved' : 'Needs Refinement'}
          </span>
        </div>
      </div>

      {/* Analyst Feedback Quote */}
      <div className="border-council-active/10 bg-council-active/5 relative rounded-xl border p-4 italic">
        <MessageSquare className="fill-council-active/10 text-council-active/20 absolute -top-3 -left-3 h-6 w-6" />
        <p className="text-sm-plus text-foreground line-clamp-3 leading-relaxed italic">
          "{validation.feedback}"
        </p>
        <div className="mt-4 flex items-center gap-2">
          <ArtifactBadge variant="active">— Analyst A2A</ArtifactBadge>
          <span className="bg-council-active/20 h-1 w-1 rounded-full" />
          <ArtifactBadge>Verified Step 4</ArtifactBadge>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="border-surface-border bg-background flex items-center justify-between rounded-xl border p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <Layers className="text-council-completed h-4 w-4" />
            <span className="text-text-muted text-xs font-bold tracking-tight uppercase">
              Conceptual Accuracy
            </span>
          </div>
          <Check className="text-success h-4 w-4" />
        </div>
        <div className="border-surface-border bg-background flex items-center justify-between rounded-xl border p-4 shadow-sm">
          <div className="flex items-center gap-3">
            <Clock className="text-council-completed h-4 w-4" />
            <span className="text-text-muted text-xs font-bold tracking-tight uppercase">
              Pacing & Flow
            </span>
          </div>
          <Check className="text-success h-4 w-4" />
        </div>
      </div>

      {validation.suggestions?.length > 0 && (
        <div className="space-y-4 pt-2">
          <div className="flex items-center gap-2">
            <Sparkles className="text-council-active h-4 w-4" />
            <h4 className="text-tiny text-text-muted font-bold tracking-[0.2em] uppercase">
              Optimization Tips
            </h4>
          </div>
          <ul className="space-y-3">
            {validation.suggestions.map((s: string, i: number) => (
              <li key={i} className="group text-text-muted flex gap-3 text-xs">
                <span className="border-council-active/20 bg-council-active/10 text-tiny text-council-active flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border font-bold">
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
