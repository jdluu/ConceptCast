import { render, screen } from '@testing-library/react';
import App from '@/App';
import { describe, it, expect } from 'vitest';

describe('App', () => {
  it('renders headline', () => {
    // Mock fetch to prevent "Invalid URL" error and network requests
    global.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        json: () => Promise.resolve({ status: 'ok', message: 'Mocked API' }),
      })
    );

    render(<App />);
    const headline = screen.getByRole('heading', { level: 1, name: /ConceptCast/i });
    expect(headline).toBeInTheDocument();
  });
});
