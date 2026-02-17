import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from '@/App'
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/api/queryClient';
import { DeveloperModeProvider } from '@/lib/contexts/developerMode';
import { AppSettingsProvider } from '@/lib/contexts/appSettings';

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
