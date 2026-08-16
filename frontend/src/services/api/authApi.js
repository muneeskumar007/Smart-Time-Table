import apiClient from "./axiosClient";

export const authApi = {
  login: (email, password, rememberMe) =>
    apiClient.post("/auth/login", { email, password, remember_me: rememberMe }).then((res) => res.data),

  refresh: () => apiClient.post("/auth/refresh").then((res) => res.data),

  logout: () => apiClient.post("/auth/logout").then((res) => res.data),

  getProfile: () => apiClient.get("/auth/me").then((res) => res.data),

  updateProfile: (payload) => apiClient.patch("/auth/me", payload).then((res) => res.data),

  changePassword: (currentPassword, newPassword) =>
    apiClient
      .post("/auth/me/change-password", { current_password: currentPassword, new_password: newPassword })
      .then((res) => res.data),
};
