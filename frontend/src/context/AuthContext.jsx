import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { authApi } from "../services/api/authApi";
import { setAccessToken, setOnRefreshFailed } from "../services/api/axiosClient";
import { getErrorMessage } from "../utils";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  // On first load there's no access token in memory (a hard refresh
  // wipes it, by design). If the browser is still holding a valid
  // httpOnly refresh-token cookie from a previous visit, this silently
  // restores the session without the user having to log in again.
  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const { data } = await authApi.refresh();
        if (cancelled) return;
        setAccessToken(data.access_token);
        setUser(data.user);
      } catch {
        // No valid session - that's fine, the person just isn't logged in.
        setAccessToken(null);
        setUser(null);
      } finally {
        if (!cancelled) setIsBootstrapping(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const clearSession = useCallback(() => {
    setAccessToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setOnRefreshFailed(clearSession);
  }, [clearSession]);

  const login = useCallback(async (email, password, rememberMe) => {
    try {
      const { data } = await authApi.login(email, password, rememberMe);
      setAccessToken(data.access_token);
      setUser(data.user);
      return { success: true };
    } catch (error) {
      return { success: false, message: getErrorMessage(error, "Incorrect email or password.") };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const updateUser = useCallback((patch) => {
    setUser((current) => (current ? { ...current, ...patch } : current));
  }, []);

  const value = {
    user,
    isAuthenticated: Boolean(user),
    isBootstrapping,
    login,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
