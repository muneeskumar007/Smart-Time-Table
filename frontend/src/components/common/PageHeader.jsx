import { cn } from "../../utils";

/**
 * @param {{title: string, subtitle?: string, action?: React.ReactNode, className?: string}} props
 */
export function PageHeader({ title, subtitle, action, className }) {
  return (
    <div className={cn("mb-6 flex flex-wrap items-start justify-between gap-3", className)}>
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
