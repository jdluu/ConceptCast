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
        <div className="max-w-2xl mx-auto px-6 py-8">
            <h1 className="text-3xl font-bold text-[var(--foreground)] mb-10 tracking-tight">Settings</h1>

            <div className="space-y-8">
                {/* UI / UX Settings */}
                <section>
                    <header className="mb-4">
                        <h2 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">UI / UX Settings</h2>
                        <p className="text-sm text-[var(--text-muted)] mt-1">Personalize your experience and improve usability.</p>
                    </header>

                    <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden backdrop-blur-sm">
                        <div className="p-6 flex items-center justify-between gap-8 border-b border-[var(--surface-border)]">
                            <div>
                                <h3 className="text-sm font-semibold text-[var(--foreground)]">Interface Theme</h3>
                                <p className="text-xs text-[var(--text-muted)] mt-1">Select your preferred color scheme for the application.</p>
                            </div>
                            
                            <div className="flex bg-[var(--background)] p-1 rounded-xl border border-[var(--surface-border)]">
                                <ThemeButton 
                                    active={theme === 'light'} 
                                    onClick={() => setTheme('light')}
                                    icon={<Sun className="w-4 h-4" />}
                                    label="Light" 
                                />
                                <ThemeButton 
                                    active={theme === 'dark'} 
                                    onClick={() => setTheme('dark')}
                                    icon={<Moon className="w-4 h-4" />}
                                    label="Dark" 
                                />
                                <ThemeButton 
                                    active={theme === 'system'} 
                                    onClick={() => setTheme('system')}
                                    icon={<Laptop className="w-4 h-4" />}
                                    label="System" 
                                />
                            </div>
                        </div>

                        <div className="p-6 flex items-center justify-between gap-8">
                            <div className="flex-1">
                                <h3 className="text-sm font-semibold text-[var(--foreground)]">Developer Mode</h3>
                                <p className="text-xs text-[var(--text-muted)] mt-1">
                                    Enables advanced features like mock data demos when API keys are missing.
                                </p>
                            </div>
                            <button
                                type="button"
                                role="switch"
                                aria-checked={developerMode}
                                onClick={() => setDeveloperMode(!developerMode)}
                                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500/50 ${
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
                        <h2 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">Accessibility & Notifications</h2>
                        <p className="text-sm text-[var(--text-muted)] mt-1">Control how the application communicates and behaves.</p>
                    </header>

                    <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden backdrop-blur-sm">
                        {/* Browser Notifications */}
                        <div className="p-6 flex items-center justify-between gap-8 border-b border-[var(--surface-border)]">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <Bell className="w-4 h-4 text-indigo-500" />
                                    <h3 className="text-sm font-semibold text-[var(--foreground)]">Completion Alerts</h3>
                                </div>
                                <p className="text-xs text-[var(--text-muted)]">
                                    Get browser notifications when a generation or rendering task completes.
                                </p>
                            </div>
                            <button
                                type="button"
                                role="switch"
                                aria-checked={settings.enableNotifications}
                                onClick={() => updateSettings({ enableNotifications: !settings.enableNotifications })}
                                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500/50 ${
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
                        <div className="p-6 flex items-center justify-between gap-8 border-b border-[var(--surface-border)]">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <Volume2 className="w-4 h-4 text-indigo-500" />
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
                                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500/50 ${
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
                        <div className="p-6 flex items-center justify-between gap-8">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <Move className="w-4 h-4 text-indigo-500" />
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
                                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500/50 ${
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
                        <h2 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">AI Orchestration</h2>
                        <p className="text-sm text-[var(--text-muted)] mt-1">Configure how the agent council operates.</p>
                    </header>

                    <div className="bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl overflow-hidden backdrop-blur-sm">
                        {/* Agent Transparency removed - managed via UI dropdowns */}
                    </div>
                </section>


                {/* Danger Zone */}
                <section>
                    <header className="mb-4">
                        <h2 className="text-xs font-bold text-red-500 uppercase tracking-[0.2em] flex items-center gap-2">
                            <Zap className="w-3 h-3" />
                            Danger Zone
                        </h2>
                    </header>

                    <div className="bg-red-500/5 border border-red-500/20 rounded-2xl overflow-hidden backdrop-blur-sm">
                        <div className="p-6 flex items-center justify-between gap-8">
                            <div className="flex-1">
                                <h3 className="text-sm font-bold text-red-500">Clear All Job History</h3>
                                <p className="text-xs text-red-500/60 mt-1">
                                    Permanently delete all generated videos, scripts, and logs. This action cannot be undone.
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
            <div className="flex items-center gap-2 animate-in fade-in slide-in-from-right-2 duration-200">
                <button
                    onClick={() => setConfirming(false)}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold text-[var(--text-muted)] hover:text-[var(--foreground)] transition-colors"
                >
                    Cancel
                </button>
                <button
                    onClick={clearHistory}
                    className="px-3 py-1.5 rounded-lg text-xs font-bold bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/20 transition-all active:scale-95"
                >
                    Confirm Delete
                </button>
            </div>
        );
    }

    return (
        <button
            onClick={() => setConfirming(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-red-500 border border-red-500/20 hover:bg-red-500/10 transition-all active:scale-95"
        >
            <Trash2 className="w-4 h-4" />
            Clear History
        </button>
    );
}

function ThemeButton({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
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
