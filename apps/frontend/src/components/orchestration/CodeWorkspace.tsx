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
    <div className="group/code border-surface-border bg-terminal-bg relative overflow-hidden rounded-xl border shadow-2xl">
      <div className="flex items-center justify-between border-b border-white/5 bg-white/5 px-4 py-2">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="bg-destructive/50 h-2 w-2 rounded-full" />
            <div className="bg-warning/50 h-2 w-2 rounded-full" />
            <div className="bg-success/50 h-2 w-2 rounded-full" />
          </div>
          <span className="text-tiny text-terminal-text/40 ml-2 font-mono tracking-widest uppercase">
            manim_scene.py
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="text-terminal-text/40 hover:text-terminal-text h-7 px-2 hover:bg-white/10"
        >
          {copied ? <Check className="text-success h-3 w-3" /> : <Copy className="h-3 w-3" />}
          <span className="text-tiny ml-1 font-bold uppercase">{copied ? 'Copied' : 'Copy'}</span>
        </Button>
      </div>

      <div className="custom-scrollbar max-h-md overflow-x-auto p-4">
        <pre className="text-mini font-mono leading-relaxed">
          <code>
            {code.split('\n').map((line, i) => (
              <div key={i} className="flex gap-4 opacity-80 transition-opacity hover:opacity-100">
                <span className="text-terminal-text/20 w-6 shrink-0 text-right select-none">
                  {i + 1}
                </span>
                <span className="text-info">
                  {line
                    .replace(/class|def|from|import/g, (m) => `\x00${m}\x00`)
                    .split('\x00')
                    .map((part, pi) =>
                      pi % 2 === 1 ? (
                        <span key={pi} className="text-council-completed">
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
