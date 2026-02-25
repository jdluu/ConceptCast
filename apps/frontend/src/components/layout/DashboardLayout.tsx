import { ReactNode, useState } from 'react';
import { Link } from '@tanstack/react-router';

const iconClass = 'w-5 h-5 shrink-0';

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
    /** The main content area of the application. */
    children: ReactNode;
}

/**
 * The primary structural component for the application dashboard.
 *
 * This component provides a consistent layout with a responsive sidebar
 * containing the main navigation links. It manages the sidebar's open/closed
 * state on mobile devices and uses TanStack Router Links for navigation.
 *
 * @param {DashboardLayoutProps} props - Component properties.
 * @returns {JSX.Element} The rendered dashboard layout.
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)] font-sans selection:bg-indigo-500/30 transition-colors duration-300">
            {/* Skip-to-content link for keyboard accessibility */}
            <a
                href="#main-content"
                className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-1/2 focus:-translate-x-1/2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-indigo-600 focus:text-white focus:rounded-xl focus:text-sm focus:font-bold focus:shadow-lg"
            >
                Skip to content
            </a>

            {/* Mobile hamburger */}
            <button
                type="button"
                aria-label="Toggle navigation menu"
                aria-expanded={sidebarOpen}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-md bg-[var(--surface)] border border-[var(--surface-border)] text-[var(--text-muted)] hover:text-[var(--foreground)] transition-colors"
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
                    className="lg:hidden fixed inset-0 z-30 bg-[var(--background)]/60 backdrop-blur-sm"
                    onClick={() => setSidebarOpen(false)}
                    aria-hidden="true"
                />
            )}

            {/* Sidebar */}
            <nav
                aria-label="Main navigation"
                className={`fixed top-0 left-0 w-64 h-full border-r border-[var(--surface-border)] bg-[var(--surface)] p-6 z-40 transition-transform duration-200 ${
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                } lg:translate-x-0`}
            >
                <div className="flex items-center gap-3 mb-10">
                    <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white text-lg shrink-0 shadow-lg shadow-indigo-500/20">
                        C
                    </div>
                    <span className="text-xl font-bold tracking-tight text-[var(--foreground)]">ConceptCast</span>
                </div>

                <div className="space-y-1" role="list">
                    <NavItem 
                        to="/" 
                        icon={<IconNewProject />} 
                        label="New Concept" 
                        onClick={() => setSidebarOpen(false)}
                    />
                    <NavItem 
                        to="/jobs" 
                        icon={<IconJobs />} 
                        label="Jobs" 
                        onClick={() => setSidebarOpen(false)}
                    />
                    <NavItem 
                        to="/library" 
                        icon={<IconLibrary />} 
                        label="Library" 
                        onClick={() => setSidebarOpen(false)}
                    />
                    <NavItem 
                        to="/settings" 
                        icon={<IconSettings />} 
                        label="Settings" 
                        onClick={() => setSidebarOpen(false)}
                    />
                </div>
            </nav>

            {/* Main content */}
            <main id="main-content" className="lg:ml-64 min-h-screen p-8 transition-colors duration-300">
                {children}
            </main>
        </div>
    );
}

/**
 * Individual navigation link displayed in the sidebar.
 */
function NavItem({ to, onClick, icon, label }: { to: any, onClick?: () => void, icon: React.ReactNode, label: string }) {
    return (
        <Link
            to={to}
            onClick={onClick}
            activeProps={{ className: 'bg-indigo-600/10 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400' }}
            inactiveProps={{ className: 'text-[var(--text-muted)] hover:text-[var(--foreground)] hover:bg-[var(--surface-border)]' }}
            className="w-full flex items-center gap-3 text-left px-3 py-2.5 rounded-xl font-medium transition-all"
        >
            {icon}
            {label}
        </Link>
    );
}
