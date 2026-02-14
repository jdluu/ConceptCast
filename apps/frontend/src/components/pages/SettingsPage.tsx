import { useDeveloperMode } from '../../lib/DeveloperModeContext';

export function SettingsPage() {
    const { developerMode, setDeveloperMode } = useDeveloperMode();

    return (
        <div className="max-w-2xl mx-auto">
            <h1 className="text-3xl font-semibold text-white mb-8">Settings</h1>

            <div className="space-y-6">
                <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                            <label htmlFor="developer-mode" className="block text-sm font-medium text-white mb-1">
                                Developer mode
                            </label>
                            <p className="text-sm text-neutral-400">
                                When enabled, shows a Run mock demo button on the New Project page when no API keys are configured.
                            </p>
                        </div>
                        <button
                            type="button"
                            id="developer-mode"
                            role="switch"
                            aria-checked={developerMode}
                            onClick={() => setDeveloperMode(!developerMode)}
                            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-black ${
                                developerMode ? 'bg-indigo-600' : 'bg-neutral-700'
                            }`}
                        >
                            <span
                                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition ${
                                    developerMode ? 'translate-x-5' : 'translate-x-1'
                                }`}
                                aria-hidden
                            />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
