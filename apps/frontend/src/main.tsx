import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '@/App'
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/api/query-client';
import { DeveloperModeProvider } from './lib/contexts/developer-mode';
import { AppSettingsProvider } from './lib/contexts/app-settings';
import '@/index.css'

import ErrorBoundary from '@/components/ErrorBoundary';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <DeveloperModeProvider>
          <AppSettingsProvider>
            <App />
          </AppSettingsProvider>
        </DeveloperModeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
