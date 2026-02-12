import { useForm, useWatch, FieldErrors, UseFormRegister } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';
import { CreateJobRequest, getAvailableModels } from '../../lib/api';
import { Button, Card } from '../ui/common';

const jobSchema = z.object({
    topic: z.string().min(3, 'Topic must be at least 3 characters'),
    target_audience: z.string().optional(),
    provider: z.string().optional(),
    model_id: z.string().optional(),
});

type JobFormData = z.infer<typeof jobSchema>;

interface JobCreationFormProps {
    onSubmit: (data: CreateJobRequest) => void;
    isLoading: boolean;
}

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

/**
 * Component for selecting the AI provider and specific model ID.
 */
const ModelSelectionFields = ({ 
    register, 
    selectedProvider, 
    availableModels 
}: { 
    register: UseFormRegister<JobFormData>; 
    selectedProvider: string | undefined; 
    availableModels: any 
}) => {
    const models = availableModels?.available
        ?.find((p: any) => p.provider === selectedProvider)
        ?.models || [];

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
                    <option value="mock">Mock (Fast)</option>
                    {availableModels?.available
                        ?.filter((p: any) => p.provider !== 'mock')
                        .map((providerGroup: any) => (
                            <option key={providerGroup.provider} value={providerGroup.provider}>
                                {providerGroup.provider.charAt(0).toUpperCase() + providerGroup.provider.slice(1)}
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
                    {selectedProvider === 'mock' && (
                        <option value="mock-llm">Mock Default</option>
                    )}
                    {models.map((model: string) => (
                        <option key={model} value={model}>{model}</option>
                    ))}
                </select>
            </div>
        </>
    );
};

/**
 * Form component for initiating a new ConceptCast generation.
 * 
 * Provides fields for topic, target audience, AI provider, and model selection.
 * Uses react-hook-form for validation and tanstack-query for model fetching.
 */
export function JobCreationForm({ onSubmit, isLoading }: JobCreationFormProps) {
    const { 
        register, 
        handleSubmit, 
        control,
        formState: { errors }
    } = useForm<JobFormData>({
        resolver: zodResolver(jobSchema),
        defaultValues: {
            topic: '',
            target_audience: 'General Audience',
            provider: 'mock', 
            model_id: 'mock-llm'
        }
    });

    const selectedProvider = useWatch({ control, name: 'provider' });

    const { data: availableModels } = useQuery({
        queryKey: ['available-models'],
        queryFn: getAvailableModels,
        staleTime: 1000 * 60 * 60, // 1 hour
    });

    const onFormSubmit = (data: JobFormData) => {
        onSubmit({
            topic: data.topic,
            target_audience: data.target_audience || 'General Audience',
            provider: data.provider || null,
            model_id: data.model_id || null,
        } as CreateJobRequest);
    };

    return (
        <Card className="max-w-xl">
            <h2 className="text-lg font-semibold mb-1 text-white">Create New Concept</h2>
            <p className="text-sm text-neutral-400 mb-6">Ask the Council to explain a topic.</p>

            <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
                <TopicField register={register} errors={errors} />

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <AudienceField register={register} />
                    <ModelSelectionFields 
                        register={register} 
                        selectedProvider={selectedProvider} 
                        availableModels={availableModels} 
                    />
                </div>

                <Button 
                    type="submit" 
                    disabled={isLoading}
                    className="w-full"
                >
                    {isLoading ? 'Consulting Council...' : 'Generate Lesson'}
                </Button>
            </form>
        </Card>
    );
}
