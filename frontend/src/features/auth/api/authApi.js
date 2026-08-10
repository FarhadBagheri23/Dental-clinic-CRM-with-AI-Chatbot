import { http } from "@/shared/api/httpClient";

export const authApi = {
  login: (username, password) => http.post("/auth/login", { username, password }),
  logout: () => http.post("/auth/logout"),
  me: (signal) => http.get("/auth/me", { signal }),
};
