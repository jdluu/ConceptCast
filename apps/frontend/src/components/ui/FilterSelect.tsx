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
    <div className="group relative">
      <div className="pointer-events-none absolute top-1/2 left-4 -translate-y-1/2 text-[var(--text-muted)] transition-colors group-hover:text-indigo-500">
        {icon}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="cursor-pointer appearance-none rounded-2xl border border-[var(--surface-border)] bg-[var(--surface)] py-3 pr-10 pl-10 text-sm font-semibold text-[var(--foreground)] shadow-sm transition-all outline-none hover:border-indigo-500/30 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/50"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 text-[var(--text-muted)] transition-colors group-hover:text-indigo-500">
        <ChevronDown className="h-4 w-4" />
      </div>
    </div>
  );
}
