import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import * as api from '../lib/api';

// Mock API
vi.mock('../lib/api', { spy: true });

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
        // Mock the available models query to avoid errors
        vi.mocked(api.getAvailableModels).mockResolvedValue({
            available: [{ provider: 'mock', models: ['mock-llm'] }]
        });
        
        renderApp();
        expect(screen.getByText('ConceptCast')).toBeInTheDocument();
    });

    it('submits a new job', async () => {
        const mockJob = {
            job_id: '123',
            status: 'planning',
            mode: 'mock',
            plan: null,
            storyboard: null,
            manim_code: null,
            video_url: null,
            error: null,
        };
        
        vi.mocked(api.createJob).mockResolvedValue(mockJob as any);
        vi.mocked(api.getJobStatus).mockResolvedValue(mockJob as any);
        vi.mocked(api.getAvailableModels).mockResolvedValue({
            available: [{ provider: 'mock', models: ['mock-llm'] }]
        });

        renderApp();

        // Fill form with topic
        fireEvent.change(screen.getByPlaceholderText(/Quantum Entanglement/i), {
            target: { value: 'Test Topic' }
        });

        // Submit
        const button = screen.getByText('Generate Lesson');
        fireEvent.click(button);

        // Verification: The Council Workflow should show the job initialized and processing
        await waitFor(() => {
            expect(screen.getByText('Council Workflow')).toBeInTheDocument();
        }, { timeout: 3000 });

        await waitFor(() => {
            expect(screen.getByText(/Job 123... initialized/i)).toBeInTheDocument();
        }, { timeout: 3000 });

        await waitFor(() => {
            expect(screen.getByText(/Processing planning/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });
});
