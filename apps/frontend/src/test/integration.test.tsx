import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from '../App';
import * as api from '../lib/api';

// Mock API
vi.mock('../lib/api', () => ({
    createJob: vi.fn(),
    getJobStatus: vi.fn(),
    getJobPlan: vi.fn(),
}));

describe('ConceptCast Dashboard', () => {
    it('renders the dashboard layout', () => {
        render(<App />);
        expect(screen.getByText('ConceptCast')).toBeInTheDocument();
        expect(screen.getByText('New Project')).toBeInTheDocument();
    });

    it('submits a new job', async () => {
        const mockJob = {
            job_id: '123',
            status: 'planning',
        };
        vi.mocked(api.createJob).mockResolvedValue(mockJob as any);
        vi.mocked(api.getJobStatus).mockResolvedValue(mockJob as any);

        render(<App />);

        // Fill form
        fireEvent.change(screen.getByPlaceholderText(/Proximal Policy Optimization/i), {
            target: { value: 'Test Topic' }
        });

        // Submit
        const button = screen.getByText('Initialize Council');
        fireEvent.click(button);

        expect(button).toBeDisabled();
        expect(screen.getByText('Consulting the Council...')).toBeInTheDocument();

        await waitFor(() => {
            expect(api.createJob).toHaveBeenCalledWith({
                topic: 'Test Topic',
                target_audience: 'Undergraduate CS'
            });
        });

        await waitFor(() => {
            expect(screen.getByText('PLANNING')).toBeInTheDocument();
        });
    });
});
