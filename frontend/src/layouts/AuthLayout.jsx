import { Outlet } from "react-router";
import { CalendarClock, CheckCircle2 } from "lucide-react";

const HIGHLIGHTS = [
  "Automatic, conflict-free timetable generation",
  "Role-based access for admins, HODs, faculty and students",
  "Live faculty workload and room utilization tracking",
];

export function AuthLayout() {
  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-brand-900 p-12 text-white lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(96,126,225,0.25),transparent_45%),radial-gradient(circle_at_80%_80%,rgba(41,81,214,0.35),transparent_45%)]" />

        <div className="relative flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10">
            <CalendarClock size={19} />
          </div>
          <span className="font-display text-lg font-bold">Smart Timetable</span>
        </div>

        <div className="relative">
          <h1 className="font-display text-3xl font-bold leading-tight">
            Department scheduling,
            <br />
            done right.
          </h1>
          <p className="mt-3 max-w-sm text-sm text-brand-100">
            One system for departments, faculty, curriculum and the weekly timetable that ties them all together.
          </p>
          <ul className="mt-8 space-y-3">
            {HIGHLIGHTS.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-brand-50">
                <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-brand-300" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-brand-300">© {new Date().getFullYear()} Smart Department Timetable Management System</p>
      </div>

      <div className="flex w-full flex-1 items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
