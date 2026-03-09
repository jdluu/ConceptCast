import { useEffect, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { motion, useReducedMotion } from 'framer-motion';
import { toast } from 'sonner';
import { getAvailableModels } from '@/lib/api/client';
import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { useJobStore } from '@/lib/store/useJobStore';
import { Button, Card } from '@/components/ui/Common';
import { AudienceField, ModelSelectionFields, QualityFields } from './JobFormFields';
import { LoadingOverlay, NoKeysAlert } from './JobFormFeedback';
import { jobSchema, JobFormData, ProviderGroup } from './JobFormTypes';

export function JobCreationForm() {
  const { developerMode } = useDeveloperMode();
  const { settings } = useAppSettings();
  const prefersReducedMotion = useReducedMotion() || settings.reducedMotion;
  const { createJob, isSubmitting: isLoading } = useJobStore();
  const [showNoKeysToast, setShowNoKeysToast] = useState(true);

  const { data: availableModels } = useQuery({
    queryKey: ['available-models'],
    queryFn: getAvailableModels,
    staleTime: 1000 * 60 * 60,
  });

  const hasRealProviders = !availableModels?.available
    ? true
    : availableModels.available.some((p: { provider: string }) => p.provider !== 'mock');

  const realProvidersOnly: ProviderGroup[] =
    availableModels?.available?.filter((p: { provider: string }) => p.provider !== 'mock') ?? [];

  const firstRealProvider = realProvidersOnly[0];
  const defaultProvider = firstRealProvider?.provider ?? '';
  const defaultModel = firstRealProvider?.models?.[0] ?? '';

  const {
    register,
    handleSubmit,
    control,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema as any),
    defaultValues: {
      topic: '',
      target_audience: 'General Audience',
      provider: 'mock',
      model_id: 'mock-llm',
      resolution: settings.resolution as '720p' | '1080p',
      frame_rate: settings.frameRate as 30 | 60,
    },
  });

  const topicInputRef = useRef<HTMLInputElement>(null);
  const { ref: topicRef, ...topicRegister } = register('topic');

  // Focus management when loading ends
  const prevLoading = useRef(isLoading);
  useEffect(() => {
    if (prevLoading.current && !isLoading) {
      topicInputRef.current?.focus();
    }
    prevLoading.current = isLoading;
  }, [isLoading]);

  const selectedProvider = useWatch({ control, name: 'provider' });
  const hasSetRealDefaults = useRef(false);

  useEffect(() => {
    if (hasRealProviders && firstRealProvider && !hasSetRealDefaults.current) {
      hasSetRealDefaults.current = true;
      setValue('provider', defaultProvider);
      setValue('model_id', defaultModel);
    }
  }, [hasRealProviders, defaultProvider, defaultModel, firstRealProvider, setValue]);

  useEffect(() => {
    if (!selectedProvider || !hasRealProviders) return;
    const models = realProvidersOnly.find((p) => p.provider === selectedProvider)?.models ?? [];
    const firstModel = models[0];
    if (firstModel) setValue('model_id', firstModel);
  }, [selectedProvider, hasRealProviders, setValue]);

  /**
   * Final form submission handler.
   * Initiates the backend generation workflow via the job store.
   *
   * @param {JobFormData} data - Validated form inputs.
   */
  const onFormSubmit = async (data: JobFormData) => {
    try {
      await createJob({
        topic: data.topic,
        target_audience: data.target_audience || 'General Audience',
        provider: data.provider || null,
        model_id: data.model_id || null,
        resolution: data.resolution,
        frame_rate: data.frame_rate as 30 | 60,
      });
      toast.success('Council consulting started!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to start generation');
    }
  };

  /**
   * Triggers a simulated generation workflow for demonstration purposes.
   */
  const runMockDemo = async () => {
    const values = getValues();
    try {
      await createJob({
        topic: values.topic || 'The Art of Modern Web Design',
        target_audience: values.target_audience || 'General Audience',
        provider: 'mock',
        model_id: 'mock-llm',
        resolution: values.resolution,
        frame_rate: values.frame_rate as 30 | 60,
      });
      toast.info('Running mock demo sequence');
    } catch {
      toast.error('Mock demo failed');
    }
  };

  const noKeys = !hasRealProviders && !!availableModels?.available?.length;
  const showMockButton = developerMode;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="relative max-w-xl overflow-hidden">
        <LoadingOverlay isLoading={isLoading} />

        <h2 className="mb-1 bg-gradient-to-r from-[var(--foreground)] to-[var(--text-muted)] bg-clip-text text-xl font-bold text-transparent">
          Create New Concept
        </h2>
        <p className="mb-8 text-sm text-[var(--text-muted)]">
          Orchestrate a pedagogical animation with the Council agents.
        </p>

        {noKeys && showNoKeysToast && (
          <NoKeysAlert developerMode={developerMode} onClose={() => setShowNoKeysToast(false)} />
        )}

        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-12">
          <div className="grid grid-cols-1 gap-x-8 gap-y-10 md:grid-cols-2">
            <section className="md:col-span-2">
              <div className="mb-4 flex items-center gap-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/10 text-xs font-bold text-indigo-500">
                  1
                </span>
                <h3 className="text-sm font-bold tracking-wider text-[var(--text-muted)] uppercase">
                  Subject Matter
                </h3>
              </div>
              <label
                htmlFor="topic"
                className="mb-2 block text-sm font-semibold text-[var(--foreground)]"
              >
                What would you like to learn?
              </label>
              <input
                {...topicRegister}
                ref={(e) => {
                  topicRef(e);
                  (topicInputRef as any).current = e;
                }}
                type="text"
                id="topic"
                className="w-full rounded-xl border border-[var(--surface-border)] bg-[var(--background)]/50 px-4 py-3.5 text-[var(--foreground)] transition-all outline-none placeholder:text-[var(--text-muted)] hover:border-indigo-500/50 focus:border-transparent focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g. Quantum Entanglement, The French Revolution..."
              />
              {errors.topic && (
                <p className="mt-2 flex items-center gap-1 text-xs font-semibold text-red-500">
                  <span className="h-1 w-1 rounded-full bg-red-500" />
                  {errors.topic.message as string}
                </p>
              )}
            </section>

            <section className="space-y-6">
              <div className="mb-1 flex items-center gap-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/10 text-xs font-bold text-indigo-500">
                  2
                </span>
                <h3 className="text-sm font-bold tracking-wider text-[var(--text-muted)] uppercase">
                  Context
                </h3>
              </div>
              <AudienceField register={register} />
              {errors.target_audience && (
                <p className="mt-1 text-xs text-red-500">
                  {errors.target_audience.message as string}
                </p>
              )}

              <QualityFields register={register} />
              {errors.resolution && (
                <p className="mt-1 text-xs text-red-500">{errors.resolution.message as string}</p>
              )}
              {errors.frame_rate && (
                <p className="mt-1 text-xs text-red-500">{errors.frame_rate.message as string}</p>
              )}
            </section>

            {hasRealProviders && (
              <section className="space-y-6">
                <div className="mb-1 flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/10 text-xs font-bold text-indigo-500">
                    3
                  </span>
                  <h3 className="text-sm font-bold tracking-wider text-[var(--text-muted)] uppercase">
                    Intelligence
                  </h3>
                </div>
                <ModelSelectionFields
                  register={register}
                  selectedProvider={selectedProvider}
                  realProvidersOnly={realProvidersOnly}
                />
                {errors.provider && (
                  <p className="mt-1 text-xs text-red-500">{errors.provider.message as string}</p>
                )}
                {errors.model_id && (
                  <p className="mt-1 text-xs text-red-500">{errors.model_id.message as string}</p>
                )}
              </section>
            )}

            {noKeys && (
              <div className="flex items-center gap-3 rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm font-medium text-amber-500 italic md:col-span-2">
                <div
                  className={`h-2 w-2 rounded-full bg-amber-500 ${prefersReducedMotion ? '' : 'animate-pulse'}`}
                />
                No real AI providers configured. Using simulated engine.
              </div>
            )}
          </div>

          <div className="flex flex-col gap-4 pt-4">
            <Button
              type="submit"
              disabled={isLoading || noKeys}
              className="h-12 w-full rounded-xl text-base font-bold shadow-lg shadow-indigo-500/20"
            >
              {isLoading ? 'Consulting Council...' : 'Generate Lesson'}
            </Button>
            {showMockButton && (
              <Button
                type="button"
                variant="outline"
                onClick={runMockDemo}
                disabled={isLoading}
                className="h-11 w-full"
              >
                Run mock demo
              </Button>
            )}
          </div>
        </form>
      </Card>
    </motion.div>
  );
}
