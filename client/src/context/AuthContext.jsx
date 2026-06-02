import { createContext, useContext, useState } from "react";
import { getToken, setToken, clearToken } from "../lib/api";

const USER_KEY = "slipstream_user";
const AuthContext = createContext(null);

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY)) || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken());
  const [user, setUser] = useState(() => readStoredUser());

  // Persist a JWT + user after a successful verify (2B will call this).
  const login = (jwt, userObj) => {
    setToken(jwt);
    setTokenState(jwt);
    if (userObj) {
      localStorage.setItem(USER_KEY, JSON.stringify(userObj));
      setUser(userObj);
    }
  };

  const logout = () => {
    clearToken();
    localStorage.removeItem(USER_KEY);
    setTokenState(null);
    setUser(null);
  };

  const value = { token, user, login, logout, isAuthenticated: !!token };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
