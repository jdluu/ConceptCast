import { useEffect, useState } from 'react';
import { listJobs, retryJob, deleteJob, type JobSummary } from '../../lib/api';

const statusColors = {
    planning: 'text-blue-400',
    validating: 'text-purple-400',
    architecting: 'text-indigo-400',
    rendering: 'text-yellow-400',
    reviewing: 'text-orange-400',
    completed: 'text-green-400',
    failed: 'text-red-400',
};

export function JobsPage() {
    const [jobs, setJobs] = useState<JobSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [retryingId, setRetryingId] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    useEffect(() => {
        loadJobs();
    }, []);

    const loadJobs = async () => {
        try {
            const response = await listJobs();
            setJobs(response.jobs);
            setError(null);
        } catch (err) {
            setError('Failed to load jobs');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = async (jobId: string) => {
        if (!confirm('Are you sure you want to retry this job? This will reset its progress from the last checkpoint.')) {
            return;
        }

        setRetryingId(jobId);
        try {
            await retryJob(jobId);
            await loadJobs();
        } catch (err) {
            alert('Failed to retry job. Check console logs.');
            console.error(err);
        } finally {
            setRetryingId(null);
        }
    };

    const handleDelete = async (jobId: string) => {
        if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
            return;
        }

        setDeletingId(jobId);
        try {
            await deleteJob(jobId);
            // Optimistic update or reload
            setJobs(jobs.filter(job => job.job_id !== jobId));
        } catch (err) {
            alert('Failed to delete job. Check console logs.');
            console.error(err);
        } finally {
            setDeletingId(null);
        }
    };

    if (loading) {
        return <div className="p-8 text-neutral-400">Loading jobs...</div>;
    }

    if (error) {
        return <div className="p-8 text-red-400">{error}</div>;
    }

    return (
        <div className="max-w-5xl mx-auto">
            <header className="mb-8">
                <h1 className="text-2xl font-semibold text-white">Job History</h1>
                <p className="text-neutral-400 mt-2">View and manage your recent generation jobs.</p>
            </header>

            <div className="overflow-x-auto rounded-lg border border-neutral-800 bg-neutral-900/50">
                <table className="w-full text-left text-sm text-neutral-300">
                    <thead className="bg-neutral-900 text-neutral-400 uppercase tracking-wider text-xs font-semibold">
                        <tr>
                            <th className="px-6 py-4">Topic</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Mode</th>
                            <th className="px-6 py-4">Retries</th>
                            <th className="px-6 py-4">Created</th>
                            <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-800">
                        {jobs.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="px-6 py-8 text-center text-neutral-500">
                                    No jobs found. Start a new project to generate content.
                                </td>
                            </tr>
                        ) : (
                            jobs.map((job) => (
                                <tr key={job.job_id} className="hover:bg-neutral-800/30 transition-colors">
                                    <td className="px-6 py-4 font-medium text-white max-w-xs truncate" title={job.topic}>
                                        {job.topic}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/5 capitalize ${statusColors[job.status] || 'text-neutral-400'}`}>
                                            {job.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 capitalize">{job.mode}</td>
                                    <td className="px-6 py-4">{job.retry_count > 0 ? job.retry_count : '-'}</td>
                                    <td className="px-6 py-4 text-neutral-500">
                                        {new Date(job.created_at).toLocaleDateString()} {new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </td>
                                    <td className="px-6 py-4 text-right space-x-3">
                                        {/* Retry Action */}
                                        {job.status === 'failed' && (
                                            <button
                                                onClick={() => handleRetry(job.job_id)}
                                                disabled={retryingId === job.job_id || deletingId === job.job_id}
                                                className="text-indigo-400 hover:text-indigo-300 transition-colors text-xs font-medium disabled:opacity-50"
                                            >
                                                {retryingId === job.job_id ? 'Retrying...' : 'Retry'}
                                            </button>
                                        )}
                                        
                                        {/* Delete Action */}
                                        <button
                                            onClick={() => handleDelete(job.job_id)}
                                            disabled={deletingId === job.job_id || retryingId === job.job_id}
                                            className="text-red-400 hover:text-red-300 transition-colors text-xs font-medium disabled:opacity-50"
                                        >
                                            {deletingId === job.job_id ? 'Deleting...' : 'Delete'}
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
