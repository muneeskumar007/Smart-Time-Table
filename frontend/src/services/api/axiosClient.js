import axios from "axios";

/**
 * The in-memory access token. Deliberately NOT persisted to
 * localStorage/sessionStorage - keeping it in memory only means it
 * disappears on a hard refresh, which is why AuthContext calls
 * POST /auth/refresh on app startup (using the httpOnly refresh-token
 * cookie the browser already holds) to silently restore the session.
 */
let accessToken = null;

/** @param {string|null} token */
export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

const apiClient = axios.create({
  baseURL: "/api/v1",
  withCredentials: true, // sends/receives the httpOnly refresh_token cookie
  timeout: 20000,
});

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// --- Automatic refresh-on-401, with a single in-flight refresh shared
// across every request that races into it (so 5 simultaneous requests
// that all 401 at once trigger exactly one /auth/refresh call, not 5).
let refreshPromise = null;
/** @type {(() => void) | null} set by AuthContext so a failed refresh can force a logout/redirect */
let onRefreshFailed = null;

/** @param {() => void} handler */
export function setOnRefreshFailed(handler) {
  onRefreshFailed = handler;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = originalRequest?.url?.startsWith("/auth/login") || originalRequest?.url?.startsWith("/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = apiClient.post("/auth/refresh").finally(() => {
            refreshPromise = null;
          });
        }
        const { data } = await refreshPromise;
        setAccessToken(data.data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.data.access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        setAccessToken(null);
        onRefreshFailed?.();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
