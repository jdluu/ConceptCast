import { useState } from 'react';

const placeholderProjects = [
    { id: '1', title: 'Quantum Physics for Kids', duration: '3:45', generated: 'Oct 26, 2023', thumbnail: '' },
    { id: '2', title: 'Intro to Machine Learning', duration: '5:12', generated: 'Oct 28, 2023', thumbnail: '' },
    { id: '3', title: 'History of Ancient Rome', duration: '4:20', generated: 'Oct 28, 2023', thumbnail: '' },
    { id: '4', title: 'How to Bake Sourdough', duration: '6:00', generated: 'Oct 29, 2023', thumbnail: '' },
    { id: '5', title: 'Understanding Blockchain', duration: '4:45', generated: 'Oct 30, 2023', thumbnail: '' },
    { id: '6', title: 'The Solar System Explained', duration: '3:30', generated: 'Oct 30, 2023', thumbnail: '' },
];

function PlayIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden>
            <path d="M8 5v14l11-7z" />
        </svg>
    );
}

function InfoIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    );
}

function TrashIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
    );
}



export function LibraryPage() {
    const [search, setSearch] = useState('');

    return (
        <div className="max-w-6xl mx-auto">
            <h1 className="text-3xl font-semibold text-white mb-8">Library</h1>

            <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <div className="relative flex-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500 pointer-events-none">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                    </span>
                    <input
                        type="search"
                        placeholder="Search projects..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 bg-neutral-900 border border-neutral-700 rounded-lg text-white placeholder:text-neutral-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                        aria-label="Search projects"
                    />
                </div>
                <div className="flex flex-wrap gap-2">
                    <select
                        aria-label="Filter by date"
                        className="px-4 py-2.5 bg-neutral-900 border border-neutral-700 rounded-lg text-neutral-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer hover:border-neutral-600 transition-colors"
                    >
                        <option>Filter by Date</option>
                    </select>
                    <select
                        aria-label="Filter by topic"
                        className="px-4 py-2.5 bg-neutral-900 border border-neutral-700 rounded-lg text-neutral-300 text-sm focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer hover:border-neutral-600 transition-colors"
                    >
                        <option>Filter by Topic</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {placeholderProjects.map((project) => (
                    <article
                        key={project.id}
                        className="group bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden flex flex-col hover:border-neutral-700 hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300"
                    >
                        <div className="aspect-video bg-neutral-800 relative flex items-center justify-center overflow-hidden">
                            <div className="absolute inset-0 bg-gradient-to-t from-neutral-900/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                            <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center text-neutral-900 shadow-lg transform group-hover:scale-110 transition-transform duration-300 z-10">
                                <PlayIcon />
                            </div>
                        </div>
                        <div className="p-5 flex-1 flex flex-col">
                            <h2 className="font-semibold text-white mb-1.5 line-clamp-2 group-hover:text-indigo-400 transition-colors">
                                {project.title}
                            </h2>
                            <div className="flex items-center gap-2 text-[11px] text-neutral-500 mb-5 font-medium uppercase tracking-wider">
                                <span>{project.duration} mins</span>
                                <span className="w-1 h-1 rounded-full bg-neutral-700" />
                                <span>{project.generated}</span>
                            </div>
                            <div className="flex gap-2 mt-auto">
                                <button
                                    type="button"
                                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
                                >
                                    <PlayIcon />
                                    Play
                                </button>
                                <button
                                    type="button"
                                    className="p-2 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-300 hover:bg-neutral-700 hover:text-white transition-all active:scale-95"
                                    aria-label="Details"
                                    title="View Plan & Storyboard"
                                >
                                    <InfoIcon />
                                </button>
                                <button
                                    type="button"
                                    className="p-2 rounded-lg bg-neutral-800 border border-neutral-700 text-neutral-300 hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400 transition-all active:scale-95"
                                    aria-label="Delete"
                                    title="Delete Project"
                                >
                                    <TrashIcon />
                                </button>
                            </div>
                        </div>
                    </article>
                ))}
            </div>
        </div>
    );
}
