import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import * as api from '../lib/api';

// Mock API
vi.mock('../lib/api', () => ({
    createJob: vi.fn(),
    getJobStatus: vi.fn(),
    getJobPlan: vi.fn(),
    getAvailableModels: vi.fn(),
}));

/**
 * Creates a fresh QueryClient for each test to avoid shared cache state.
 */
function createTestQueryClient(): QueryClient {
    return new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });
}

/**
 * Renders the App wrapped in a fresh QueryClientProvider.
 */
function renderApp() {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <App />
        </QueryClientProvider>
    );
}

describe('ConceptCast Dashboard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the dashboard layout', () => {
        renderApp();
        expect(screen.getByText('ConceptCast')).toBeInTheDocument();
    });

    it('submits a new job', async () => {
        const mockJob = {
            job_id: '123',
            status: 'planning',
        };
        vi.mocked(api.createJob).mockResolvedValue(mockJob as any);
        vi.mocked(api.getJobStatus).mockResolvedValue(mockJob as any);

        renderApp();

        // Fill form with topic
        fireEvent.change(screen.getByPlaceholderText(/Quantum Entanglement/i), {
            target: { value: 'Test Topic' }
        });

        // Submit
        const button = screen.getByText('Generate Lesson');
        fireEvent.click(button);

        expect(button).toBeDisabled();
        expect(screen.getByText('Consulting Council...')).toBeInTheDocument();

        await waitFor(() => {
            expect(api.createJob).toHaveBeenCalledWith({
                topic: 'Test Topic',
                target_audience: 'General Audience',
                provider: 'mock',
                model_id: 'llama3-70b-8192',
            });
        });

        await waitFor(() => {
            expect(screen.getByText('PLANNING')).toBeInTheDocument();
        });
    });
});

