import { NavLink } from "react-router";
import * as Icons from "lucide-react";
import { X } from "lucide-react";
import { NAV_ITEMS } from "../constants";
import { useAuth } from "../context/AuthContext";
import { cn } from "../utils";

/**
 * @param {{ isMobileOpen: boolean, onCloseMobile: () => void }} props
 */
export function Sidebar({ isMobileOpen, onCloseMobile }) {
  const { user } = useAuth();
  const items = NAV_ITEMS.filter((item) => item.roles.includes(user?.role));

  return (
    <>
      {isMobileOpen && (
        <div className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden" onClick={onCloseMobile} aria-hidden="true" />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform duration-200 dark:border-slate-800 dark:bg-slate-900 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 shrink-0 items-center justify-between px-5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Icons.CalendarClock size={17} />
            </div>
            <span className="font-display text-sm font-bold leading-tight text-slate-900 dark:text-white">
              Smart
              <br />
              Timetable
            </span>
          </div>
          <button onClick={onCloseMobile} className="text-slate-400 lg:hidden" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2 scrollbar-thin" aria-label="Main navigation">
          {items.map((item) => {
            const Icon = Icons[item.icon] ?? Icons.Circle;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                      : "text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                  )
                }
              >
                <Icon size={17} className="shrink-0" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-slate-100 p-4 dark:border-slate-800">
          <p className="text-xs text-slate-400 dark:text-slate-500">Smart Department Timetable v1.0</p>
        </div>
      </aside>
    </>
  );
}
