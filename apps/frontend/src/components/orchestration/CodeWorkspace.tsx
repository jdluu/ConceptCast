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
    <div className="group/code relative overflow-hidden rounded-xl border border-[var(--surface-border)] bg-[#1e1e1e]">
      <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="h-2 w-2 rounded-full bg-red-500/50" />
            <div className="h-2 w-2 rounded-full bg-amber-500/50" />
            <div className="h-2 w-2 rounded-full bg-emerald-500/50" />
          </div>
          <span className="ml-2 font-mono text-[10px] tracking-widest text-white/40 uppercase">
            manim_scene.py
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 px-2 text-white/40 hover:bg-white/10 hover:text-white"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
          <span className="ml-1 text-[10px] font-bold uppercase">{copied ? 'Copied' : 'Copy'}</span>
        </Button>
      </div>

      <div className="custom-scrollbar max-h-[400px] overflow-x-auto p-4">
        <pre className="font-mono text-[11px] leading-relaxed">
          <code>
            {code.split('\n').map((line, i) => (
              <div key={i} className="flex gap-4 opacity-80 transition-opacity hover:opacity-100">
                <span className="w-6 shrink-0 text-right text-white/20 select-none">{i + 1}</span>
                <span className="text-blue-300">
                  {line
                    .replace(/class|def|from|import/g, (m) => `\x00${m}\x00`)
                    .split('\x00')
                    .map((part, pi) =>
                      pi % 2 === 1 ? (
                        <span key={pi} className="text-purple-400">
                          {part}
                        </span>
                      ) : (
                        part
                      ),
                    )}
                </span>
              </div>
            ))}
          </code>
        </pre>
      </div>
    </div>
  );
}
