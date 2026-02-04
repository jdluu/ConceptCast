import { useState } from 'react';
import { CreateJobRequest } from '../../lib/api';
import { Button, Card } from '../ui/common';

export function JobCreationForm({ onSubmit, isLoading }: { 
    onSubmit: (data: CreateJobRequest) => void;
    isLoading: boolean;
}) {
    const [topic, setTopic] = useState('');
    const [audience, setAudience] = useState('Undergraduate CS');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({ topic, target_audience: audience });
    };

    return (
        <Card className="max-w-xl">
            <h2 className="text-lg font-semibold mb-1 text-white">Create New Concept</h2>
            <p className="text-sm text-neutral-400 mb-6">Ask the Council to explain a topic.</p>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-1">
                        Topic
                    </label>
                    <input
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="e.g. Proximal Policy Optimization"
                        className="w-full bg-neutral-950 border border-neutral-800 rounded-md px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
                        required
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-neutral-300 mb-1">
                        Target Audience
                    </label>
                    <select
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
