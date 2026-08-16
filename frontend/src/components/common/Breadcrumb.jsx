import { Link, useLocation } from "react-router";
import { ChevronRight, Home } from "lucide-react";
import { NAV_ITEMS } from "../../constants";

const EXTRA_LABELS = {
  "/profile": "My Profile",
  "/settings": "Settings",
  "/unauthorized": "Access Restricted",
};

function labelForPath(path) {
  const navMatch = NAV_ITEMS.find((item) => item.path === path);
  if (navMatch) return navMatch.label;
  return EXTRA_LABELS[path] ?? path;
}

export function Breadcrumb() {
  const { pathname } = useLocation();

  if (pathname === "/dashboard") return null;

  const label = labelForPath(pathname);

  return (
    <nav aria-label="Breadcrumb" className="mb-4 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
      <Link to="/dashboard" className="flex items-center gap-1 hover:text-brand-600 dark:hover:text-brand-400">
        <Home size={13} />
        Dashboard
      </Link>
      <ChevronRight size={13} className="text-slate-300 dark:text-slate-600" />
      <span aria-current="page" className="font-medium text-slate-700 dark:text-slate-200">
        {label}
      </span>
    </nav>
  );
}
