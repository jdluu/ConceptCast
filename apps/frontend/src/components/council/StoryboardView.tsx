import { Storyboard, Scene } from '../../lib/api';

interface StoryboardViewProps {
    storyboard: Storyboard;
}

/**
 * StoryboardView component.
 * 
 * Displays the visual orchestration as a series of scene cards.
 */
export function StoryboardView({ storyboard }: StoryboardViewProps) {
    return (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h3 className="text-md font-semibold text-white mb-4">Visual Storyboard</h3>
            <div className="space-y-6">
                {storyboard.scenes.map((scene: Scene) => (
                    <div key={scene.scene_id} className="bg-neutral-950 p-4 rounded-lg border border-neutral-800 space-y-3">
                        <div className="flex justify-between items-start">
                            <div>
                                <span className="text-xs font-mono text-indigo-500 uppercase tracking-wider">Scene {scene.scene_id}</span>
                                <h4 className="text-sm font-medium text-white">{scene.title}</h4>
                            </div>
                        </div>
                        
                        <p className="text-xs text-neutral-400 italic">"{scene.description}"</p>
                        
                        <div className="bg-black/50 p-3 rounded border border-neutral-800/50">
                            <div className="text-[10px] uppercase text-neutral-500 mb-2 font-bold tracking-tight">Visual Objects</div>
                            <div className="flex flex-wrap gap-2">
                                {scene.objects.map((obj, i) => (
                                    <div key={i} className="px-2 py-1 bg-neutral-900 rounded text-[10px] border border-neutral-700 font-mono text-neutral-300">
                                        <span className="text-indigo-400">{obj.type}</span>: {obj.name}
                                        {obj.label && <span className="text-neutral-500"> ({obj.label})</span>}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="text-xs text-neutral-300 bg-indigo-500/5 p-2 rounded border border-indigo-500/10">
                            <span className="font-bold text-indigo-400 mr-2">NARRATION:</span>
                            {scene.narration}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
