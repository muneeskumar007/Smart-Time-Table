import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "../context/AuthContext";
import { PageLoader } from "../components/common/LoadingState";

/** Blocks unauthenticated users, redirecting to /login (preserving where they were headed). */
export function RequireAuth() {
  const { isAuthenticated, isBootstrapping } = useAuth();
  const location = useLocation();

  if (isBootstrapping) return <PageLoader />;
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location }} replace />;
  return <Outlet />;
}

/** Sends an already-logged-in user away from /login straight to their dashboard. */
export function RedirectIfAuthenticated() {
  const { isAuthenticated, isBootstrapping } = useAuth();
  if (isBootstrapping) return <PageLoader />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

/**
 * @param {{ roles: string[] }} props
 */
export function RequireRole({ roles }) {
  const { user } = useAuth();
  if (!roles.includes(user?.role)) return <Navigate to="/unauthorized" replace />;
  return <Outlet />;
}
