import { useRef, useEffect } from 'react';

interface VideoPreviewProps {
    videoUrl: string;
    conceptTitle: string;
}

/**
 * VideoPreview component.
 * 
 * Displays the final rendered MP4 animation.
 */
export function VideoPreview({ videoUrl, conceptTitle }: VideoPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null);

    // Auto-play when URL changes
    useEffect(() => {
        if (videoRef.current) {
            videoRef.current.load();
        }
    }, [videoUrl]);

    return (
        <div className="bg-neutral-900 border border-indigo-500/30 rounded-lg p-6 shadow-2xl shadow-indigo-500/10 transition-all hover:border-indigo-500/50">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-md font-semibold text-white">Final Render</h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500 text-white uppercase tracking-widest">
                    480p • 15fps
                </span>
            </div>
            
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-neutral-800 ring-1 ring-white/5">
                <video 
                    ref={videoRef}
                    className="w-full h-full object-contain"
                    controls
                    autoPlay
                    loop
                >
                    <source src={videoUrl} type="video/mp4" />
                    Your browser does not support the video tag.
                </video>
            </div>
            
            <div className="mt-4 flex items-center justify-between">
                <div>
                    <div className="text-xs font-medium text-white">{conceptTitle}</div>
                    <div className="text-[10px] text-neutral-500 font-mono mt-1">{videoUrl.split('/').pop()}</div>
                </div>
                <a 
                    href={videoUrl} 
                    download 
                    className="inline-flex items-center px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-[10px] font-semibold rounded transition-colors border border-neutral-700"
                >
                    Download MP4
                </a>
            </div>
        </div>
    );
}
