import { createContext, useCallback, useEffect, useMemo, useState } from "react";

import { authApi } from "@/features/auth/api/authApi";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // The session lives in an httpOnly cookie, so JS cannot read it — the only
  // way to know whether one exists is to ask the server. Until that answers,
  // the app must render neither the login page nor the panel, or a reloading
  // user gets bounced to the login screen they were already past.
  const [status, setStatus] = useState("loading"); // loading | authenticated | anonymous

  useEffect(() => {
    const controller = new AbortController();
    authApi
      .me(controller.signal)
      .then((data) => {
        setUser(data);
        setStatus("authenticated");
      })
      .catch((error) => {
        if (error.name === "AbortError") return;
        setStatus("anonymous");
      });
    return () => controller.abort();
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await authApi.login(username, password);
    setUser(data);
    setStatus("authenticated");
    return data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      // Clear locally even if the request failed — leaving a stale user in
      // state shows a panel whose every request will 401.
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  const value = useMemo(() => ({ user, status, login, logout }), [user, status, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
