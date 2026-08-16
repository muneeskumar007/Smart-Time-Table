import { cn } from "../../utils";

const VARIANTS = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300",
  success: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  warning: "bg-accent-50 text-accent-700 dark:bg-accent-950/40 dark:text-accent-300",
  danger: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
};

/**
 * @param {{variant?: keyof typeof VARIANTS, dot?: boolean} & React.HTMLAttributes<HTMLSpanElement>} props
 */
export function Badge({ variant = "neutral", dot = false, className, children, ...props }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        VARIANTS[variant],
        className
      )}
      {...props}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

/** Maps the common is_active boolean straight to a consistent badge. */
export function ActiveBadge({ isActive }) {
  return (
    <Badge variant={isActive ? "success" : "neutral"} dot>
      {isActive ? "Active" : "Inactive"}
    </Badge>
  );
}
