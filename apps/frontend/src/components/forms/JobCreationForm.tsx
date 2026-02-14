import { useEffect, useRef, useState } from 'react';
import { useForm, useWatch, FieldErrors, UseFormRegister } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { getAvailableModels } from '../../lib/api';
import { useDeveloperMode } from '../../lib/DeveloperModeContext';
import { useJobStore } from '../../lib/store/useJobStore';
import { Button, Card } from '../ui/common';

const jobSchema = z.object({
    topic: z.string().min(3, 'Topic must be at least 3 characters'),
    target_audience: z.string().optional(),
    provider: z.string().optional(),
    model_id: z.string().optional(),
});

type JobFormData = z.infer<typeof jobSchema>;

interface FieldProps {
    register: UseFormRegister<JobFormData>;
    errors: FieldErrors<JobFormData>;
}

const TopicField = ({ register, errors }: FieldProps) => (
    <div>
        <label htmlFor="topic" className="block text-sm font-medium text-neutral-300 mb-1">
            What would you like to learn?
        </label>
        <input
            {...register('topic')}
            type="text"
            id="topic"
            className="w-full bg-neutral-950 border border-neutral-800 rounded px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all placeholder:text-neutral-600"
            placeholder="e.g. Quantum Entanglement, The French Revolution..."
        />
        {errors.topic && (
            <p className="mt-1 text-sm text-red-400">{errors.topic.message as string}</p>
        )}
    </div>
);

const AudienceField = ({ register }: { register: UseFormRegister<JobFormData> }) => (
    <div>
        <label htmlFor="target_audience" className="block text-sm font-medium text-neutral-300 mb-1">
            Target Audience
        </label>
        <select
            {...register('target_audience')}
            id="target_audience"
            className="w-full bg-neutral-950 border border-neutral-800 rounded px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
        >
            <option value="5-year-old">5-year-old</option>
            <option value="High School Student">High School Student</option>
            <option value="University Student">University Student</option>
            <option value="Expert">Expert</option>
            <option value="General Audience">General Audience</option>
        </select>
    </div>
);

type ProviderGroup = { provider: string; display_name?: string | null; models: string[] };

const ModelSelectionFields = ({
    register,
    selectedProvider,
    realProvidersOnly,
}: {
    register: UseFormRegister<JobFormData>;
    selectedProvider: string | undefined;
    realProvidersOnly: ProviderGroup[];
}) => {
    const models =
        realProvidersOnly.find((p) => p.provider === selectedProvider)?.models ?? [];

    return (
        <>
            <div>
                <label htmlFor="provider" className="block text-sm font-medium text-neutral-300 mb-1">
                    AI Provider
                </label>
                <select
                    {...register('provider')}
                    id="provider"
                    className="w-full bg-neutral-950 border border-neutral-800 rounded px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 outline-none"
                >
                    {realProvidersOnly.map((providerGroup) => (
                        <option key={providerGroup.provider} value={providerGroup.provider}>
                            {providerGroup.display_name ??
                                providerGroup.provider.charAt(0).toUpperCase() + providerGroup.provider.slice(1)}
                        </option>
                    ))}
                </select>
            </div>

            <div>
                <label htmlFor="model_id" className="block text-sm font-medium text-neutral-300 mb-1">
                    Model
                </label>
                <select
                    {...register('model_id')}
                    id="model_id"
                    className="w-full bg-neutral-950 border border-neutral-800 rounded px-4 py-2 text-white focus:ring-2 focus:ring-indigo-500 outline-none disabled:opacity-50"
                    disabled={!selectedProvider}
                >
                    {models.map((model: string) => (
                        <option key={model} value={model}>
                            {model}
                        </option>
                    ))}
                </select>
            </div>
        </>
    );
};

const LoadingOverlay = ({ isLoading }: { isLoading: boolean }) => (
    <AnimatePresence>
        {isLoading && (
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-neutral-900/80 backdrop-blur-md z-50 flex flex-col items-center justify-center gap-4"
            >
                <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full" 
                />
                <motion.p 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-white font-semibold tracking-wide uppercase text-sm"
                >
                    Summoning the Council...
                </motion.p>
            </motion.div>
        )}
    </AnimatePresence>
);

const NoKeysAlert = ({ 
    developerMode, 
    onClose 
}: { 
    developerMode: boolean; 
    onClose: () => void;
}) => (
    <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: 'auto' }}
        className="mb-8 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-200 text-sm flex items-start justify-between gap-4"
        role="alert"
    >
        <span>
            {developerMode
                ? 'No API keys configured. Add keys to generate lessons, or run a mock demo below.'
                : 'No API keys configured. Add keys in your environment, or enable Developer mode in Settings to run a mock demo.'}
        </span>
        <button
            type="button"
            onClick={onClose}
            className="shrink-0 text-amber-400/60 hover:text-amber-300 rounded p-0.5 transition-colors"
        >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    </motion.div>
);

export function JobCreationForm() {
    const { developerMode } = useDeveloperMode();
    const { createJob, isSubmitting: isLoading } = useJobStore();
    const [showNoKeysToast, setShowNoKeysToast] = useState(true);

    const { data: availableModels } = useQuery({
        queryKey: ['available-models'],
        queryFn: getAvailableModels,
        staleTime: 1000 * 60 * 60,
    });

    const hasRealProviders =
        !availableModels?.available
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
        resolver: zodResolver(jobSchema),
        defaultValues: {
            topic: '',
            target_audience: 'General Audience',
            provider: 'mock',
            model_id: 'mock-llm',
        },
    });

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

    const onFormSubmit = async (data: JobFormData) => {
        try {
            await createJob({
                topic: data.topic,
                target_audience: data.target_audience || 'General Audience',
                provider: data.provider || null,
                model_id: data.model_id || null,
            });
            toast.success('Council consulting started!');
        } catch (err: any) {
            toast.error(err.message || 'Failed to start generation');
        }
    };

    const runMockDemo = async () => {
        const values = getValues();
        try {
            await createJob({
                topic: values.topic || 'The Art of Modern Web Design',
                target_audience: values.target_audience || 'General Audience',
                provider: 'mock',
                model_id: 'mock-llm',
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
            <Card className="max-w-xl relative overflow-hidden">
                <LoadingOverlay isLoading={isLoading} />

                <h2 className="text-xl font-bold mb-1 text-white">Create New Concept</h2>
                <p className="text-sm text-neutral-400 mb-8">Ask the Council to explain a topic in depth.</p>

                {noKeys && showNoKeysToast && (
                    <NoKeysAlert 
                        developerMode={developerMode} 
                        onClose={() => setShowNoKeysToast(false)} 
                    />
                )}

                <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-8">
                    <TopicField register={register} errors={errors} />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <AudienceField register={register} />
                        {hasRealProviders && (
                            <ModelSelectionFields
                                register={register}
                                selectedProvider={selectedProvider}
                                realProvidersOnly={realProvidersOnly}
                            />
                        )}
                        {noKeys && (
                            <div className="md:col-span-2 flex items-center gap-2 text-neutral-500 text-sm font-medium italic">
                                <span className="w-1.5 h-1.5 rounded-full bg-neutral-700" />
                                No providers configured
                            </div>
                        )}
                    </div>

                    <div className="flex flex-col gap-4 pt-4">
                        <Button
                            type="submit"
                            disabled={isLoading || noKeys}
                            className="w-full h-12 text-base font-bold shadow-indigo-500/20 shadow-lg"
                        >
                            {isLoading ? 'Consulting Council...' : 'Generate Lesson'}
                        </Button>
                        {showMockButton && (
                            <Button
                                type="button"
                                onClick={runMockDemo}
                                disabled={isLoading}
                                className="w-full h-11 border-2 border-indigo-500 bg-transparent text-indigo-400 hover:bg-indigo-500/5 hover:text-indigo-300 transition-all font-semibold"
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
