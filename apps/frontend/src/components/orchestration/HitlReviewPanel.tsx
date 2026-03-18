import { useState } from 'react';
import { CurriculumPlan, JobReviewRequest, reviewJob } from '@/lib/api/client';
import { Button } from '@/components/ui/Common';
import { Card } from '@/components/ui/Card';
import { Check, RefreshCw, MessageSquare, Edit3 } from 'lucide-react';
import { toast } from 'sonner';

interface HitlReviewPanelProps {
  jobId: string;
  plan: CurriculumPlan;
  onActionComplete: () => void;
}

export function HitlReviewPanel({ jobId, plan, onActionComplete }: HitlReviewPanelProps) {
  const [editedPlan, setEditedPlan] = useState<CurriculumPlan>({ ...plan });
  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const handleAction = async (action: 'approve' | 'regenerate') => {
    setIsSubmitting(true);
    try {
      const request: JobReviewRequest = {
        action,
        feedback: action === 'regenerate' ? feedback : undefined,
        edited_plan: action === 'approve' && isEditing ? editedPlan : undefined,
      };

      await reviewJob(jobId, request);
      toast.success(action === 'approve' ? 'Plan approved!' : 'Regeneration started.');
      onActionComplete();
    } catch (error) {
      console.error('Review failed:', error);
      toast.error('Failed to process review action.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateStep = (index: number, field: string, value: string) => {
    const newSteps = [...editedPlan.teaching_steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    setEditedPlan({ ...editedPlan, teaching_steps: newSteps });
    setIsEditing(true);
  };

  return (
    <Card
      variant="premium"
      className="animate-in fade-in zoom-in-95 border-council-active/30 mt-8 p-6 duration-300"
    >
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-foreground text-lg font-bold">Human Review Required</h2>
          <p className="text-text-muted text-sm">
            The Analyst has proposed a curriculum. Review and refine it below.
          </p>
        </div>
        <div className="bg-council-active/10 text-council-active flex h-10 w-10 items-center justify-center rounded-full">
          <MessageSquare className="h-5 w-5" />
        </div>
      </header>

      <div className="space-y-4">
        {editedPlan.teaching_steps.map((step, idx) => (
          <div
            key={idx}
            className="group border-surface-border bg-background/50 hover:border-council-active/30 relative rounded-xl border p-4 transition-colors"
          >
            <div className="mb-2 flex items-center gap-3">
              <span className="bg-council-active/10 text-council-active flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold">
                {idx + 1}
              </span>
              <input
                className="text-foreground focus:text-council-active flex-1 bg-transparent font-semibold outline-none"
                value={step.concept}
                onChange={(e) => updateStep(idx, 'concept', e.target.value)}
              />
            </div>
            <textarea
              className="text-text-muted focus:text-foreground w-full bg-transparent text-sm outline-none"
              rows={2}
              value={step.narration}
              onChange={(e) => updateStep(idx, 'narration', e.target.value)}
            />
            <div className="text-tiny text-text-muted mt-2 flex items-center gap-2 font-medium opacity-0 transition-opacity group-hover:opacity-100">
              <Edit3 className="h-3 w-3" />
              <span>Editing enabled</span>
            </div>
          </div>
        ))}
      </div>

      <div className="border-surface-border mt-8 space-y-6 border-t pt-6">
        <div>
          <label className="text-foreground mb-2 block text-sm font-semibold">
            Steer the Agent (Optional)
          </label>
          <textarea
            className="border-surface-border bg-background/50 text-foreground focus:border-council-active/50 focus:ring-council-active/20 w-full rounded-xl border p-4 text-sm transition-all outline-none focus:ring-2"
            placeholder="e.g. 'Make step 3 more detailed about the physics...'"
            rows={3}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
        </div>

        <div className="flex gap-4">
          <Button
            variant="outline"
            className="flex-1 gap-2"
            onClick={() => handleAction('regenerate')}
            disabled={isSubmitting}
          >
            <RefreshCw className={`h-4 w-4 ${isSubmitting ? 'animate-spin' : ''}`} />
            Regenerate with Feedback
          </Button>
          <Button
            className="flex-1 gap-2"
            onClick={() => handleAction('approve')}
            disabled={isSubmitting}
          >
            <Check className="h-4 w-4" />
            {isEditing ? 'Save Edits & Approve' : 'Approve & Proceed'}
          </Button>
        </div>
      </div>
    </Card>
  );
}
