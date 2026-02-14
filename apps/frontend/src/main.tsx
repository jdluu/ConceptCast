import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '@/App'
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { DeveloperModeProvider } from './lib/DeveloperModeContext';
import '@/index.css'

import ErrorBoundary from '@/components/ErrorBoundary';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <DeveloperModeProvider>
          <App />
        </DeveloperModeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
