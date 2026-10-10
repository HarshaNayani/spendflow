import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import api from "../api";

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem("sf_user"));
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser);

  const saveSession = useCallback((data) => {
    localStorage.setItem("sf_token", data.access_token);
    localStorage.setItem("sf_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("sf_token");
    localStorage.removeItem("sf_user");
    setUser(null);
  }, []);

  const login = useCallback(
    async (email, password) => {
      const { data } = await api.post("/auth/login", { email, password });
      return saveSession(data);
    },
    [saveSession]
  );

  const register = useCallback(
    async (name, email, password) => {
      const { data } = await api.post("/auth/register", { name, email, password });
      return saveSession(data);
    },
    [saveSession]
  );

  // The API client fires this event when the server rejects the token.
  useEffect(() => {
    window.addEventListener("sf-unauthorized", logout);
    return () => window.removeEventListener("sf-unauthorized", logout);
  }, [logout]);

  const value = useMemo(
    () => ({ user, login, register, logout }),
    [user, login, register, logout]
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
