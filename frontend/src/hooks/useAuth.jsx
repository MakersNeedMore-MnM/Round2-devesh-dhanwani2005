import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { AuthAPI } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("cs_token");
    const cached = localStorage.getItem("cs_user");
    if (cached) {
      try {
        setUser(JSON.parse(cached));
      } catch {
        localStorage.removeItem("cs_user");
      }
    }
    if (!token) {
      setLoading(false);
      return;
    }
    AuthAPI.me()
      .then((profile) => {
        setUser(profile);
        localStorage.setItem("cs_user", JSON.stringify(profile));
      })
      .catch(() => {
        localStorage.removeItem("cs_token");
        localStorage.removeItem("cs_user");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      async login(email, password) {
        const result = await AuthAPI.login(email, password);
        localStorage.setItem("cs_token", result.access_token);
        localStorage.setItem("cs_user", JSON.stringify(result.user));
        setUser(result.user);
        return result.user;
      },
      async logout() {
        try {
          await AuthAPI.logout();
        } catch {
          /* session already gone */
        }
        localStorage.removeItem("cs_token");
        localStorage.removeItem("cs_user");
        setUser(null);
      },
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
