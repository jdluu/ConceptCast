import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface CodeWorkspaceProps {
    /** The source code string to display. */
    code: string;
}

/**
 * A code viewer with line numbers, basic syntax highlighting for
 * Python keywords, and a copy-to-clipboard button.
 *
 * @param {CodeWorkspaceProps} props - Component properties.
 * @returns {JSX.Element} The rendered code workspace.
 */
export function CodeWorkspace({ code }: CodeWorkspaceProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative rounded-xl overflow-hidden border border-[var(--surface-border)] bg-[#1e1e1e] group/code">
            <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-2">
                    <div className="flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-red-500/50" />
                        <div className="w-2 h-2 rounded-full bg-amber-500/50" />
                        <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
                    </div>
                    <span className="text-[10px] font-mono text-white/40 ml-2 uppercase tracking-widest">manim_scene.py</span>
                </div>
                <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={handleCopy}
                    className="h-7 px-2 text-white/40 hover:text-white hover:bg-white/10"
                >
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span className="text-[10px] font-bold uppercase ml-1">{copied ? 'Copied' : 'Copy'}</span>
                </Button>
            </div>
            
            <div className="p-4 overflow-x-auto max-h-[400px] custom-scrollbar">
                <pre className="text-[11px] font-mono leading-relaxed">
                    <code>
                        {code.split('\n').map((line, i) => (
                            <div key={i} className="flex gap-4 opacity-80 hover:opacity-100 transition-opacity">
                                <span className="w-6 shrink-0 text-right text-white/20 select-none">{i + 1}</span>
                                <span className="text-blue-300">
                                    {line.replace(/class|def|from|import/g, (m) => `\x00${m}\x00`)
                                         .split('\x00').map((part, pi) => (
                                             pi % 2 === 1 ? <span key={pi} className="text-purple-400">{part}</span> : part
                                         ))}
                                </span>
                            </div>
                        ))}
                    </code>
                </pre>
            </div>
        </div>
    );
}
