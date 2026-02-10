import { ReactNode, useState } from 'react';

/**
 * Provides the primary application layout and navigation structure.
 *
 * Implements a responsive sidebar that is persistent on large screens
 * and collapsible (via hamburger menu) on mobile devices.
 *
 * @param props.children - The main content to be displayed within the layout.
 */
export function DashboardLayout({ children }: { children: ReactNode }) {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen bg-black text-neutral-200 font-sans selection:bg-indigo-500/30">
            {/* Mobile hamburger button */}
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

            {/* Mobile overlay */}
            {sidebarOpen && (
                <div
                    className="lg:hidden fixed inset-0 z-30 bg-black/60"
                    onClick={() => setSidebarOpen(false)}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar / Navigation */}
            <nav
                aria-label="Main navigation"
                className={`fixed top-0 left-0 w-64 h-full border-r border-neutral-800 bg-neutral-950 p-6 z-40 transition-transform duration-200 ${
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                } lg:translate-x-0`}
            >
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-white">
                        C
                    </div>
                    <span className="text-xl font-bold tracking-tight">ConceptCast</span>
                </div>

                <div className="space-y-1" role="list">
                    <button
                        type="button"
                        aria-current="page"
                        className="w-full text-left px-3 py-2 rounded-md bg-neutral-900 text-white font-medium"
                    >
                        New Project
                    </button>
                    <button
                        type="button"
                        disabled
                        className="w-full text-left px-3 py-2 rounded-md text-neutral-500 hover:text-neutral-300 disabled:cursor-not-allowed"
                    >
                        History
                    </button>
                    <button
                        type="button"
                        disabled
                        className="w-full text-left px-3 py-2 rounded-md text-neutral-500 hover:text-neutral-300 disabled:cursor-not-allowed"
                    >
                        Settings
                    </button>
                </div>
            </nav>

            {/* Main Content */}
            <main className="lg:ml-64 p-8 max-w-5xl mx-auto">
                <h1 className="sr-only">ConceptCast Dashboard</h1>
                {children}
            </main>
        </div>
    );
}
