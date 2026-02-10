import { useState, useEffect } from 'react';
import { CreateJobRequest, getAvailableModels, ProviderModels } from '../../lib/api';
import { Button, Card } from '../ui/common';

/**
 * Form component for initializing a new ConceptCast job.
 *
 * Handles provider and model discovery, validation, and submission of
 * topic/audience data to the backend.
 *
 * @param props - Component props.
 * @param props.onSubmit - Callback triggered upon valid form submission.
 * @param props.isLoading - Boolean indicating if a job is currently being initialized.
 */
export function JobCreationForm({ onSubmit, isLoading }: { 
    onSubmit: (data: CreateJobRequest) => void;
    isLoading: boolean;
}) {
    const [topic, setTopic] = useState('');
    const [audience, setAudience] = useState('Undergraduate CS');
    const [availableProviders, setAvailableProviders] = useState<ProviderModels[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<string>('');
    const [selectedModel, setSelectedModel] = useState<string>('');

    useEffect(() => {
        getAvailableModels().then(data => {
            setAvailableProviders(data.available);
        }).catch(() => {
            // Model loading failed silently; form will show fallback text
        });
    }, []);

    /**
     * Updates the selected provider and resets the associated model to the default.
     *
     * @param provider - The selected AI provider ID.
     */
    const handleProviderChange = (provider: string) => {
        setSelectedProvider(provider);
        const models = availableProviders.find(p => p.provider === provider)?.models || [];
        setSelectedModel(models[0] || '');
    };

    /**
     * Prevents default form behavior and propagates submission data.
     *
     * @param e - The form submission event.
     */
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ 
            topic, 
            target_audience: audience,
            provider: selectedProvider || undefined,
            model_id: selectedModel || undefined
        });
    };

    const currentModels = availableProviders.find(p => p.provider === selectedProvider)?.models || [];

    return (
        <Card className="max-w-xl">
            <h2 className="text-lg font-semibold mb-1 text-white">Create New Concept</h2>
            <p className="text-sm text-neutral-400 mb-6">Ask the Council to explain a topic.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label htmlFor="topic" className="block text-sm font-medium text-neutral-300 mb-1">
                        Topic
                    </label>
                    <input
                        id="topic"
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g. Proximal Policy Optimization"
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                        required
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label htmlFor="provider" className="block text-sm font-medium text-neutral-300 mb-1">
                            Provider (Optional)
                        </label>
                        <select
                            id="provider"
                            value={selectedProvider}
                            onChange={(e) => handleProviderChange(e.target.value)}
                            className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none capitalize"
                        >
                            <option value="">{availableProviders.length > 0 ? "Auto-Select (Smart)" : "Loading Providers..."}</option>
                            {availableProviders.map(p => (
                                <option key={p.provider} value={p.provider}>{p.provider}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label htmlFor="model" className="block text-sm font-medium text-neutral-300 mb-1">
                            Model
                        </label>
                        <select
                            id="model"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            disabled={!selectedProvider}
                            className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none disabled:opacity-50"
                        >
                            {!selectedProvider && <option value="">Select Provider first</option>}
                            {currentModels.map(m => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                    </div>
                </div>

                <div>
                    <label htmlFor="audience" className="block text-sm font-medium text-neutral-300 mb-1">
                        Target Audience
                    </label>
                    <select
                        id="audience"
                        value={audience}
                        onChange={(e) => setAudience(e.target.value)}
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                    >
                        <option>High School Student</option>
                        <option>Undergraduate CS</option>
                        <option>PhD Researcher</option>
                        <option>5 Year Old</option>
                    </select>
                </div>

                <div className="pt-2">
                    <Button type="submit" disabled={isLoading} className="w-full">
                        {isLoading ? 'Consulting the Council...' : 'Initialize Council'}
                    </Button>
                </div>
            </form>
        </Card>
    );
}
