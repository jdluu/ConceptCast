import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { CreateJobRequest } from '../../lib/api';
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

export function JobCreationForm({ onSubmit, isLoading }: JobCreationFormProps) {
    const { 
        register, 
        handleSubmit, 
        formState: { errors }
    } = useForm<JobFormData>({
        resolver: zodResolver(jobSchema),
        defaultValues: {
            topic: '',
            target_audience: 'General Audience',
            provider: 'mock', 
            model_id: 'llama3-70b-8192'
        }
    });



    return (
        <Card className="max-w-xl">
            <h2 className="text-lg font-semibold mb-1 text-white">Create New Concept</h2>
            <p className="text-sm text-neutral-400 mb-6">Ask the Council to explain a topic.</p>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
                        <p className="mt-1 text-sm text-red-400">{errors.topic.message}</p>
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                            <option value="groq">Groq</option>
                            <option value="google">Google Gemini</option>
                            <option value="deepseek">DeepSeek</option>
                        </select>
                    </div>
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
