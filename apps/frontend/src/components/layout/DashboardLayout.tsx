import { ReactNode } from 'react';

export function DashboardLayout({ children }: { children: ReactNode }) {
    return (
        <div className="min-h-screen bg-black text-neutral-200 font-sans selection:bg-indigo-500/30">
            {/* Sidebar / Navigation */}
            <nav className="fixed top-0 left-0 w-64 h-full border-r border-neutral-800 bg-neutral-950 p-6">
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center font-bold text-white">
                        C
                    </div>
                    <span className="text-xl font-bold tracking-tight">ConceptCast</span>
                </div>

                <div className="space-y-1">
                    <div className="px-3 py-2 rounded-md bg-neutral-900 text-white font-medium">
                        New Project
                    </div>
                    <div className="px-3 py-2 rounded-md text-neutral-500 hover:text-neutral-300 cursor-not-allowed">
                        History
                    </div>
                    <div className="px-3 py-2 rounded-md text-neutral-500 hover:text-neutral-300 cursor-not-allowed">
                        Settings
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="ml-64 p-8 max-w-5xl mx-auto">
                {children}
            </main>
        </div>
    );
}
