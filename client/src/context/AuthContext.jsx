import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken, clearToken } from "../lib/api";

const USER_KEY = "slipstream_user";
const AuthContext = createContext(null);

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY)) || null;
  } catch {
    return null;
  }
}

function storeUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(() => getToken());
  const [user, setUser] = useState(() => readStoredUser());

  // Persist a JWT + user after a successful magic-link verify.
  const login = useCallback((jwt, userObj) => {
    setToken(jwt);
    setTokenState(jwt);
    if (userObj) {
      storeUser(userObj);
      setUser(userObj);
    }
  }, []);

  const logout = useCallback(() => {
    clearToken();
    localStorage.removeItem(USER_KEY);
    setTokenState(null);
    setUser(null);
  }, []);

  // Refresh the profile (incl. bank balance) whenever we hold a token. An
  // expired/invalid token gets a 401, which api.js turns into a sign-out.
  useEffect(() => {
    if (!token) return;
    let active = true;
    api
      .get("/auth/me")
      .then((me) => {
        if (!active) return;
        storeUser(me);
        setUser(me);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [token]);

  const value = { token, user, login, logout, isAuthenticated: !!token };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
