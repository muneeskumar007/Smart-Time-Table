import { Loader2 } from "lucide-react";
import { cn } from "../../utils";

/** @param {{className?: string}} props */
export function Spinner({ className }) {
  return <Loader2 className={cn("animate-spin text-brand-600", className)} size={20} />;
}

/** @param {{ rows?: number, columns?: number }} props */
export function TableSkeleton({ rows = 6, columns = 5 }) {
  return (
    <div className="animate-pulse divide-y divide-slate-100 dark:divide-slate-800">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex items-center gap-4 px-4 py-3.5">
          {Array.from({ length: columns }).map((__, c) => (
            <div
              key={c}
              className="h-4 rounded bg-slate-200 dark:bg-slate-700"
              style={{ width: c === 0 ? "20%" : `${60 / columns}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/** @param {{ className?: string, count?: number }} props */
export function CardSkeleton({ className, count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={cn("animate-pulse rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900", className)}>
          <div className="h-4 w-1/3 rounded bg-slate-200 dark:bg-slate-700" />
          <div className="mt-3 h-7 w-1/2 rounded bg-slate-200 dark:bg-slate-700" />
        </div>
      ))}
    </>
  );
}

/** Full-page centred spinner, for route-level Suspense fallbacks. */
export function PageLoader() {
  return (
    <div className="flex h-full min-h-[50vh] w-full items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  );
}
