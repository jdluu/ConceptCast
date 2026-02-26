import { ChevronDown } from 'lucide-react';

interface FilterSelectProps {
    /** Icon node rendered inside the left edge of the select. */
    icon: React.ReactNode;
    /** Current selected value. */
    value: string;
    /** Callback fired when the selection changes. */
    onChange: (v: string) => void;
    /** Available options to choose from. */
    options: { label: string; value: string }[];
}

/**
 * Styled select dropdown with a leading icon and custom chevron.
 *
 * @param {FilterSelectProps} props - Component properties.
 * @returns {JSX.Element} The rendered filter select.
 */
export function FilterSelect({ icon, value, onChange, options }: FilterSelectProps) {
    return (
        <div className="relative group">
            <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)] group-hover:text-indigo-500 transition-colors pointer-events-none">
                {icon}
            </div>
            <select 
                value={value} 
                onChange={(e) => onChange(e.target.value)}
                className="pl-10 pr-10 py-3 bg-[var(--surface)] border border-[var(--surface-border)] rounded-2xl text-sm font-semibold text-[var(--foreground)] focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 outline-none appearance-none cursor-pointer hover:border-indigo-500/30 transition-all shadow-sm"
            >
                {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <div className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)] pointer-events-none group-hover:text-indigo-500 transition-colors">
                <ChevronDown className="w-4 h-4" />
            </div>
        </div>
    );
}
