import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../App';
import * as api from '../lib/api';
import { DeveloperModeProvider } from '../lib/DeveloperModeContext';

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
 * Renders the App wrapped in QueryClientProvider and DeveloperModeProvider.
 */
function renderApp() {
    const queryClient = createTestQueryClient();
    return render(
        <QueryClientProvider client={queryClient}>
            <DeveloperModeProvider>
                <App />
            </DeveloperModeProvider>
        </QueryClientProvider>
    );
}

describe('ConceptCast Dashboard', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders the dashboard layout', () => {
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
        // Provide a real provider so "Generate Lesson" is enabled (mock is filtered out when has real providers)
        vi.mocked(api.getAvailableModels).mockResolvedValue({
            available: [
                { provider: 'google', models: ['gemini-2.5-flash'], display_name: 'Google (Gemini)' },
                { provider: 'mock', models: ['mock-llm'] }
            ]
        });

        renderApp();

        fireEvent.change(screen.getByPlaceholderText(/Quantum Entanglement/i), {
            target: { value: 'Test Topic' }
        });

        const button = screen.getByText('Generate Lesson');
        fireEvent.click(button);

        // Verification: Generating view shows with System Logs and proper topic
        await waitFor(() => {
            expect(screen.getByText('System Logs')).toBeInTheDocument();
            expect(screen.getByText('Test Topic')).toBeInTheDocument();
        }, { timeout: 3000 });

        await waitFor(() => {
            expect(screen.getByText(/Analyst: Creating curriculum plan/i)).toBeInTheDocument();
        }, { timeout: 3000 });
    });
});
