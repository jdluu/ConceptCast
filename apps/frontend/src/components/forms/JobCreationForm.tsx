import { useEffect, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { LazyMotion, domAnimation } from 'motion/react';
import * as m from 'motion/react-m';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { getAvailableModels, type JobRequest } from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { useJobStore } from '@/lib/store/useJobStore';
import { Button } from '@/components/ui/Common';
import { Card } from '@/components/ui/Card';
import {
  ModelSelectionFields,
  AgentModelSelectionFields,
} from '@/components/forms/JobFormFields';
import { LoadingOverlay, NoKeysAlert } from '@/components/forms/JobFormFeedback';
import { JobFormData, jobSchema } from '@/components/forms/JobFormTypes';

function FormSection({
  number,
  title,
  children,
  className = '',
}: {
  number: number;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={cn('space-y-6', className)}>
      <div className="mb-4 flex items-center gap-3">
        <span className="bg-council-active/10 text-council-active flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold">
          {number}
        </span>
        <h3 className="text-text-muted text-sm font-bold tracking-wider uppercase">{title}</h3>
      </div>
      {children}
    </section>
  );
}

export function JobCreationForm() {
  const { developerMode } = useDeveloperMode();
  const { settings } = useAppSettings();
  const { createJob, isSubmitting: isLoading } = useJobStore();

  const [showNoKeysToast, setShowNoKeysToast] = useState(true);
  const topicInputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    setValue,
    control,
    formState: { errors },
  } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      provider: 'mock',
      model_id: 'mock-gpt-4',
    },
  });

  const selectedProvider = useWatch({ control, name: 'provider' });

  const { data } = useQuery({
    queryKey: ['models'],
    queryFn: getAvailableModels,
    staleTime: 1000 * 60 * 5,
  });

  const providers = data?.available ?? [];
  const realProvidersOnly = providers.filter((p) => p.provider !== 'mock');
  const hasRealProviders = realProvidersOnly.length > 0;
  const noKeys = !hasRealProviders;

  useEffect(() => {
    if (hasRealProviders && selectedProvider === 'mock') {
      const firstReal = realProvidersOnly[0];
      setValue('provider', firstReal.provider);
      setValue('model_id', firstReal.models[0]);
    }
  }, [hasRealProviders, selectedProvider, realProvidersOnly, setValue]);

  const onFormSubmit = async (formData: JobFormData) => {
    try {
      const request: JobRequest = {
        topic: formData.topic,
        provider: formData.provider,
        model_id: formData.model_id,
        analyst_model: formData.analyst_model || undefined,
        architect_model: formData.architect_model || undefined,
        animator_model: formData.animator_model || undefined,
      };
      await createJob(request);
    } catch (error) {
      console.error('Submission failed:', error);
      toast.error('Failed to start generation. Check your connection.');
    }
  };

  const runMockDemo = () => {
    createJob({
      topic: 'Quantum Entanglement',
      provider: 'mock',
      model_id: 'mock-gpt-4',
    });
  };

  const showMockButton = developerMode;
  const { ref: topicRef, ...topicRegister } = register('topic');

  return (
    <LazyMotion features={domAnimation}>
      <m.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <Card variant="premium" className="relative max-w-xl overflow-hidden p-8">
          <LoadingOverlay isLoading={isLoading} />

          <h2 className="from-foreground to-text-muted mb-1 bg-gradient-to-r bg-clip-text text-xl font-bold text-transparent">
            Create New Concept
          </h2>
          <p className="text-text-muted mb-8 text-sm">
            Generate an educational animation with the Council agents.
          </p>

          {noKeys && showNoKeysToast && (
            <NoKeysAlert developerMode={developerMode} onClose={() => setShowNoKeysToast(false)} />
          )}

          <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-12">
            <div className="grid grid-cols-1 gap-x-8 gap-y-10 md:grid-cols-2">
              <FormSection number={1} title="Subject Matter" className="md:col-span-2">
                <div className="space-y-2">
                  <label htmlFor="topic" className="text-foreground block text-sm font-semibold">
                    What would you like to learn?
                  </label>
                  <input
                    {...topicRegister}
                    ref={(e) => {
                      topicRef(e);
                      topicInputRef.current = e;
                    }}
                    type="text"
                    id="topic"
                    className="border-surface-border bg-background/50 text-foreground placeholder:text-text-muted hover:border-council-active/50 focus:ring-council-active w-full rounded-xl border px-4 py-3.5 transition-all outline-none focus:border-transparent focus:ring-2"
                    placeholder="e.g. Quantum Entanglement, The French Revolution..."
                  />
                  {errors.topic && (
                    <p className="text-destructive flex items-center gap-1 text-xs font-semibold">
                      <span className="bg-destructive h-1 w-1 rounded-full" />
                      {errors.topic.message as string}
                    </p>
                  )}
                </div>
              </FormSection>

              <FormSection number={2} title="Context">
                <div className="space-y-6" />
              </FormSection>

              {hasRealProviders && (
                <FormSection number={3} title="Intelligence" className="md:col-span-2">
                  <div className="space-y-8">
                    <ModelSelectionFields
                      register={register}
                      selectedProvider={selectedProvider}
                      realProvidersOnly={realProvidersOnly}
                    />

                    {settings.showAdvancedModelSettings && (
                      <div className="border-surface-border animate-in fade-in slide-in-from-top-2 mt-6 border-t pt-6 duration-300">
                        <div className="mb-4">
                          <h4 className="text-council-active text-xs font-bold tracking-widest uppercase">
                            Manual Model Overrides
                          </h4>
                          <p className="text-micro text-text-muted mt-1">
                            Configure specific models for each stage of the generation pipeline.
                          </p>
                        </div>
                        <AgentModelSelectionFields
                          register={register}
                          providers={realProvidersOnly}
                        />
                      </div>
                    )}
                  </div>
                </FormSection>
              )}

              {noKeys && (
                <div className="border-warning/20 bg-warning/5 text-warning flex items-center gap-3 rounded-xl border p-4 text-sm font-medium italic md:col-span-2">
                  <div className={`bg-warning h-2 w-2 animate-pulse rounded-full`} />
                  No real AI providers configured. Using simulated engine.
                </div>
              )}
            </div>

            <div className="flex flex-col gap-4 pt-4">
              <Button type="submit" disabled={isLoading || noKeys} className="w-full">
                {isLoading ? 'Consulting Council...' : 'Generate Lesson'}
              </Button>
              {showMockButton && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={runMockDemo}
                  disabled={isLoading}
                  className="w-full"
                >
                  Run mock demo
                </Button>
              )}
            </div>
          </form>
        </Card>
      </m.div>
    </LazyMotion>
  );
}
