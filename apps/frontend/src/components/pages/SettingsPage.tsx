import { useDeveloperMode } from '@/lib/contexts/developerMode';
import { useTheme } from '@/lib/contexts/theme';
import { useAppSettings } from '@/lib/contexts/appSettings';
import { Moon, Sun, Laptop, Zap, Trash2, Bell, Volume2, Move } from 'lucide-react';
import { useState } from 'react';
import { deleteAllJobs } from '@/lib/api/client';

export function SettingsPage() {
  const { developerMode, setDeveloperMode } = useDeveloperMode();
  const { theme, setTheme } = useTheme();
  const { settings, updateSettings } = useAppSettings();

  return (
    <div className="mx-auto max-w-2xl px-6 py-8">
      <h1 className="text-foreground mb-10 text-3xl font-bold tracking-tight">Settings</h1>

      <div className="space-y-8">
        {/* UI / UX Settings */}
        <section>
          <header className="mb-4">
            <h2 className="text-tiny text-text-muted font-bold tracking-[0.2em] uppercase">
              UI / UX Settings
            </h2>
            <p className="text-text-muted mt-1 text-sm">
              Personalize your experience and improve usability.
            </p>
          </header>

          <div className="border-surface-border bg-surface overflow-hidden rounded-2xl border backdrop-blur-sm">
            <div className="border-surface-border flex items-center justify-between gap-8 border-b p-6">
              <div>
                <h3 className="text-foreground text-sm font-semibold">Interface Theme</h3>
                <p className="text-text-muted mt-1 text-xs">
                  Select your preferred color scheme for the application.
                </p>
              </div>

              <div className="border-surface-border bg-background flex rounded-xl border p-1">
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
                <h3 className="text-foreground text-sm font-semibold">Developer Mode</h3>
                <p className="text-text-muted mt-1 text-xs">
                  Enables advanced features like mock data demos when API keys are missing.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={developerMode}
                onClick={() => setDeveloperMode(!developerMode)}
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  developerMode ? 'bg-council-active' : 'bg-surface-border'
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
            <h2 className="text-tiny text-text-muted font-bold tracking-[0.2em] uppercase">
              Accessibility & Notifications
            </h2>
            <p className="text-text-muted mt-1 text-sm">
              Control how the application communicates and behaves.
            </p>
          </header>

          <div className="border-surface-border bg-surface overflow-hidden rounded-2xl border backdrop-blur-sm">
            {/* Browser Notifications */}
            <div className="border-surface-border flex items-center justify-between gap-8 border-b p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Bell className="text-council-active h-4 w-4" />
                  <h3 className="text-foreground text-sm font-semibold">Completion Alerts</h3>
                </div>
                <p className="text-text-muted text-xs">
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
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  settings.enableNotifications ? 'bg-council-active' : 'bg-surface-border'
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
            <div className="border-surface-border flex items-center justify-between gap-8 border-b p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Volume2 className="text-council-active h-4 w-4" />
                  <h3 className="text-foreground text-sm font-semibold">Sound Effects</h3>
                </div>
                <p className="text-text-muted text-xs">
                  Play subtle audio cues for status updates and completion.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.enableSound}
                onClick={() => updateSettings({ enableSound: !settings.enableSound })}
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  settings.enableSound ? 'bg-council-active' : 'bg-surface-border'
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
                  <Move className="text-council-active h-4 w-4" />
                  <h3 className="text-foreground text-sm font-semibold">Reduced Motion</h3>
                </div>
                <p className="text-text-muted text-xs">
                  Disable intensive UI animations and pulsing indicators.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.reducedMotion}
                onClick={() => updateSettings({ reducedMotion: !settings.reducedMotion })}
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  settings.reducedMotion ? 'bg-council-active' : 'bg-surface-border'
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
            <h2 className="text-tiny text-text-muted font-bold tracking-[0.2em] uppercase">
              AI Orchestration
            </h2>
            <p className="text-text-muted mt-1 text-sm">
              Configure how the agent council operates.
            </p>
          </header>

          <div className="border-surface-border bg-surface overflow-hidden rounded-2xl border backdrop-blur-sm">
            <div className="flex items-center justify-between gap-8 p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Move className="text-council-active h-4 w-4" />
                  <h3 className="text-foreground text-sm font-semibold">Human in the Loop</h3>
                </div>
                <p className="text-text-muted text-xs">
                  Pause after curriculum planning to review, edit, or steer the plan.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.hitlEnabled}
                onClick={() => updateSettings({ hitlEnabled: !settings.hitlEnabled })}
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  settings.hitlEnabled ? 'bg-council-active' : 'bg-surface-border'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    settings.hitlEnabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            <div className="border-surface-border flex items-center justify-between gap-8 border-t p-6">
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <Zap className="text-council-active h-4 w-4" />
                  <h3 className="text-foreground text-sm font-semibold">
                    Advanced Model Configuration
                  </h3>
                </div>
                <p className="text-text-muted text-xs">
                  Enable granular model selection for each agent in the Council.
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={settings.showAdvancedModelSettings}
                onClick={() =>
                  updateSettings({ showAdvancedModelSettings: !settings.showAdvancedModelSettings })
                }
                className={`focus:ring-council-active/50 relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:ring-2 focus:outline-none ${
                  settings.showAdvancedModelSettings ? 'bg-council-active' : 'bg-surface-border'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    settings.showAdvancedModelSettings ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>
          </div>
        </section>

        {/* Danger Zone */}
        <section>
          <header className="mb-4">
            <h2 className="text-tiny text-destructive flex items-center gap-2 font-bold tracking-[0.2em] uppercase">
              <Zap className="h-3 w-3" />
              Danger Zone
            </h2>
          </header>

          <div className="border-destructive/20 bg-destructive/5 overflow-hidden rounded-2xl border backdrop-blur-sm">
            <div className="flex items-center justify-between gap-8 p-6">
              <div className="flex-1">
                <h3 className="text-destructive text-sm font-bold">Clear All Job History</h3>
                <p className="text-destructive/60 mt-1 text-xs">
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

  const clearHistory = async () => {
    try {
      await deleteAllJobs();
      window.location.reload();
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
          className="text-text-muted hover:text-foreground rounded-lg px-3 py-1.5 text-xs font-bold transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={clearHistory}
          className="bg-destructive shadow-destructive/20 hover:bg-destructive/90 rounded-lg px-3 py-1.5 text-xs font-bold text-white shadow-lg transition-all active:scale-95"
        >
          Confirm Delete
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setConfirming(true)}
      className="border-destructive/20 text-destructive hover:bg-destructive/10 flex items-center gap-2 rounded-xl border px-4 py-2 text-xs font-bold transition-all active:scale-95"
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
        active ? 'bg-council-active text-white shadow-lg' : 'text-text-muted hover:text-foreground'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
