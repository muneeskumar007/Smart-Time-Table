import { cn } from "../../utils";

/**
 * @param {{className?: string, padded?: boolean} & React.HTMLAttributes<HTMLDivElement>} props
 */
export function Card({ className, padded = true, children, ...props }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-900/[0.03]",
        "dark:border-slate-800 dark:bg-slate-900",
        padded && "p-5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action, className }) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-3", className)}>
      <div>
        <h3 className="font-display text-base font-semibold text-slate-900 dark:text-white">{title}</h3>
        {subtitle && <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

/** A single stat tile for the dashboard grid. */
export function StatCard({ label, value, icon: Icon, accent = "brand", isLoading }) {
  const accentClasses = {
    brand: "bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-400",
    emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400",
    amber: "bg-accent-50 text-accent-600 dark:bg-accent-950/40 dark:text-accent-400",
    rose: "bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-400",
  };

  return (
    <Card className="flex items-center gap-4">
      <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl", accentClasses[accent])}>
        {Icon && <Icon size={20} />}
      </div>
      <div className="min-w-0">
        <p className="truncate text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
        {isLoading ? (
          <div className="mt-1.5 h-6 w-14 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        ) : (
          <p className="font-display text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
        )}
      </div>
    </Card>
  );
}
