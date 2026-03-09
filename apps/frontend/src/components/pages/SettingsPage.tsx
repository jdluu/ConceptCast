import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useTheme } from '@/lib/contexts/theme';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { Moon, Sun, Laptop, Zap, Trash2, Bell, Volume2, Move } from 'lucide-react';
import { useState } from 'react';

export function SettingsPage() {
  const { developerMode, setDeveloperMode } = useDeveloperMode();
  const { theme, setTheme } = useTheme();
  const { settings, updateSettings } = useAppSettings();

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="mb-10 text-3xl font-bold tracking-tight text-[var(--foreground)]">Settings</h1>

      <div className="space-y-8">
        {/* UI / UX Settings */}
        <section>
          <header className="mb-4">
            <h2 className="text-xs font-bold tracking-[0.2em] text-[var(--text-muted)] uppercase">
              UI / UX Settings
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Personalize your experience and improve usability.
            </p>
          </header>

          <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] backdrop-blur-sm">
            <div className="flex items-center justify-between gap-8 border-b border-[var(--surface-border)] p-6">
              <div>
                <h3 className="text-sm font-semibold text-[var(--foreground)]">Interface Theme</h3>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  Select your preferred color scheme for the application.
                </p>
              </div>

              <div className="flex rounded-xl border border-[var(--surface-border)] bg-[var(--background)] p-1">
                <ThemeButton
                  active={theme === 'light'}
                  onClick={() => setTheme('light')}
                  icon={<Sun className="h-4 w-4" />}
                  label="Light"
                />
                <ThemeButton
                  active={theme === 'dark'}
                  onClick={() => setTheme('dark')}
                  icon={<Moon className="h-4 w-4" />}
                  label="Dark"
                />
                <ThemeButton
                  active={theme === 'system'}
                  onClick={() => setTheme('system')}
                  icon={<Laptop className="h-4 w-4" />}
                  label="System"
                />
              </div>
            </div>

            <div className="flex items-center justify-between gap-8 p-6">
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-[var(--foreground)]">Developer Mode</h3>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  Enables advanced features like mock data demos when API keys are missing.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={developerMode}
                onClick={() => setDeveloperMode(!developerMode)}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500/50 focus:outline-none ${
                  developerMode ? 'bg-indigo-600' : 'bg-[var(--surface-border)]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    developerMode ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* Accessibility & Notifications */}
        <section>
          <header className="mb-4">
            <h2 className="text-xs font-bold tracking-[0.2em] text-[var(--text-muted)] uppercase">
              Accessibility & Notifications
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Control how the application communicates and behaves.
            </p>
          </header>

          <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] backdrop-blur-sm">
            {/* Browser Notifications */}
            <div className="flex items-center justify-between gap-8 border-b border-[var(--surface-border)] p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Bell className="h-4 w-4 text-indigo-500" />
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">
                    Completion Alerts
                  </h3>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  Get browser notifications when a generation or rendering task completes.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.enableNotifications}
                onClick={() =>
                  updateSettings({ enableNotifications: !settings.enableNotifications })
                }
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500/50 focus:outline-none ${
                  settings.enableNotifications ? 'bg-indigo-600' : 'bg-[var(--surface-border)]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    settings.enableNotifications ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Sound Effects */}
            <div className="flex items-center justify-between gap-8 border-b border-[var(--surface-border)] p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Volume2 className="h-4 w-4 text-indigo-500" />
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">Sound Effects</h3>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  Play subtle audio cues for status updates and completion.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.enableSound}
                onClick={() => updateSettings({ enableSound: !settings.enableSound })}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500/50 focus:outline-none ${
                  settings.enableSound ? 'bg-indigo-600' : 'bg-[var(--surface-border)]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    settings.enableSound ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Reduced Motion */}
            <div className="flex items-center justify-between gap-8 p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Move className="h-4 w-4 text-indigo-500" />
                  <h3 className="text-sm font-semibold text-[var(--foreground)]">Reduced Motion</h3>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  Disable intensive UI animations and pulsing indicators.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.reducedMotion}
                onClick={() => updateSettings({ reducedMotion: !settings.reducedMotion })}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:ring-indigo-500/50 focus:outline-none ${
                  settings.reducedMotion ? 'bg-indigo-600' : 'bg-[var(--surface-border)]'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    settings.reducedMotion ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* AI Orchestration */}
        <section>
          <header className="mb-4">
            <h2 className="text-xs font-bold tracking-[0.2em] text-[var(--text-muted)] uppercase">
              AI Orchestration
            </h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">
              Configure how the agent council operates.
            </p>
          </header>

          <div className="overflow-hidden rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] backdrop-blur-sm">
            {/* Agent Transparency removed - managed via UI dropdowns */}
          </div>
        </section>

        {/* Danger Zone */}
        <section>
          <header className="mb-4">
            <h2 className="flex items-center gap-2 text-xs font-bold tracking-[0.2em] text-red-500 uppercase">
              <Zap className="h-3 w-3" />
              Danger Zone
            </h2>
          </header>

          <div className="overflow-hidden rounded-2xl border border-red-500/20 bg-red-500/5 backdrop-blur-sm">
            <div className="flex items-center justify-between gap-8 p-6">
              <div className="flex-1">
                <h3 className="text-sm font-bold text-red-500">Clear All Job History</h3>
                <p className="mt-1 text-xs text-red-500/60">
                  Permanently delete all generated videos, scripts, and logs. This action cannot be
                  undone.
                </p>
              </div>
              <ClearHistoryButton />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function ClearHistoryButton() {
  const [confirming, setConfirming] = useState(false);

  // Placeholder mutation - needs backend implementation
  const clearHistory = async () => {
    try {
      await fetch('http://localhost:8000/jobs', { method: 'DELETE' });
      window.location.reload(); // Simple reload to clear state for now
    } catch (e) {
      console.error('Failed to clear history:', e);
      setConfirming(false);
    }
  };

  if (confirming) {
    return (
      <div className="animate-in fade-in slide-in-from-right-2 flex items-center gap-2 duration-200">
        <button
          onClick={() => setConfirming(false)}
          className="rounded-lg px-3 py-1.5 text-xs font-bold text-[var(--text-muted)] transition-colors hover:text-[var(--foreground)]"
        >
          Cancel
        </button>
        <button
          onClick={clearHistory}
          className="rounded-lg bg-red-600 px-3 py-1.5 text-xs font-bold text-white shadow-lg shadow-red-600/20 transition-all hover:bg-red-700 active:scale-95"
        >
          Confirm Delete
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="flex items-center gap-2 rounded-xl border border-red-500/20 px-4 py-2 text-xs font-bold text-red-500 transition-all hover:bg-red-500/10 active:scale-95"
    >
      <Trash2 className="h-4 w-4" />
      Clear History
    </button>
  );
}

function ThemeButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
        active
          ? 'bg-indigo-600 text-white shadow-lg'
          : 'text-[var(--text-muted)] hover:text-[var(--foreground)]'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
