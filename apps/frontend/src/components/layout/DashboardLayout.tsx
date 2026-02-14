import { ReactNode, useState } from 'react';
import { useNavStore } from '../../lib/store/useNavStore';

const iconClass = 'w-5 h-5 shrink-0';

export type NavId = 'new-project' | 'jobs' | 'library' | 'settings';

function IconNewProject() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    );
}

function IconJobs() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
    );
}

function IconLibrary() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
    );
}

function IconSettings() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
    );
}

interface DashboardLayoutProps {
    children: ReactNode;
}

/**
 * Provides the primary application layout and navigation structure.
 *
 * Sidebar: circular logo, app name, and nav items (New Project, Jobs, Library, Settings).
 * No Templates, no user profile. Responsive: collapsible on mobile via hamburger.
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
    const { currentNav, setCurrentNav } = useNavStore();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen bg-black text-neutral-200 font-sans selection:bg-indigo-500/30">
            {/* Mobile hamburger */}
            <button
                type="button"
                aria-label="Toggle navigation menu"
                aria-expanded={sidebarOpen}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-neutral-900 border border-neutral-700 text-neutral-300 hover:text-white transition-colors"
            >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                    {sidebarOpen ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                </svg>
            </button>

            {sidebarOpen && (
                <div
                    className="lg:hidden fixed inset-0 z-30 bg-black/60"
                    onClick={() => setSidebarOpen(false)}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar */}
            <nav
                aria-label="Main navigation"
                className={`fixed top-0 left-0 w-64 h-full border-r border-neutral-800 bg-neutral-950 p-6 z-40 transition-transform duration-200 ${
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                } lg:translate-x-0`}
            >
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-lg shrink-0">
                        C
                    </div>
                    <span className="text-xl font-bold tracking-tight text-white">ConceptCast</span>
                </div>

                <div className="space-y-1" role="list">
                    <button
                        type="button"
                        aria-current={currentNav === 'new-project' ? 'page' : undefined}
                        onClick={() => setCurrentNav('new-project')}
                        className={`w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-md font-medium transition-colors ${
                            currentNav === 'new-project'
                                ? 'bg-neutral-800/80 text-white'
                                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                        }`}
                    >
                        <IconNewProject />
                        New Project
                    </button>
                    <button
                        type="button"
                        aria-current={currentNav === 'jobs' ? 'page' : undefined}
                        onClick={() => setCurrentNav('jobs')}
                        className={`w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-md font-medium transition-colors ${
                            currentNav === 'jobs'
                                ? 'bg-neutral-800/80 text-white'
                                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                        }`}
                    >
                        <IconJobs />
                        Jobs
                    </button>
                    <button
                        type="button"
                        aria-current={currentNav === 'library' ? 'page' : undefined}
                        onClick={() => setCurrentNav('library')}
                        className={`w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-md font-medium transition-colors ${
                            currentNav === 'library'
                                ? 'bg-neutral-800/80 text-white'
                                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                        }`}
                    >
                        <IconLibrary />
                        Library
                    </button>
                    <button
                        type="button"
                        aria-current={currentNav === 'settings' ? 'page' : undefined}
                        onClick={() => setCurrentNav('settings')}
                        className={`w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-md font-medium transition-colors ${
                            currentNav === 'settings'
                                ? 'bg-neutral-800/80 text-white'
                                : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                        }`}
                    >
                        <IconSettings />
                        Settings
                    </button>
                </div>
            </nav>

            {/* Main content */}
            <main className="lg:ml-64 min-h-screen p-8">
                {children}
            </main>
        </div>
    );
}
