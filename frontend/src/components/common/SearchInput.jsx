import { useEffect, useState } from "react";
import { Search, X } from "lucide-react";
import { useDebounce } from "../../hooks/useDebounce";

/**
 * Uncontrolled-feeling search box that debounces before calling
 * onChange, so list pages don't fire a request per keystroke.
 * @param {{ value: string, onChange: (value: string) => void, placeholder?: string, className?: string }} props
 */
export function SearchInput({ value, onChange, placeholder = "Search…", className }) {
  const [draft, setDraft] = useState(value ?? "");
  const debounced = useDebounce(draft, 350);

  useEffect(() => {
    onChange(debounced);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  useEffect(() => {
    if (value === "") setDraft("");
  }, [value]);

  return (
    <div className={className}>
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          aria-label={placeholder}
          className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-8 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
        />
        {draft && (
          <button
            onClick={() => setDraft("")}
            aria-label="Clear search"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
