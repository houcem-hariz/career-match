"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  getMe,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
} from "@/lib/api";

export interface User {
  email: string;
  name: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  /** Throws ApiError (401 bad credentials, 400 invalid email). */
  login: (email: string, password: string) => Promise<void>;
  /** Throws ApiError (409 already registered, 400 short password). */
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Bumped after login/register: the session may have been hydrated from the account. */
  sessionVersion: number;
  openLoginModal: () => void;
  closeLoginModal: () => void;
  isLoginModalOpen: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function toUser(email: string | null): User | null {
  if (!email) return null;
  return { email, name: email.split("@")[0] || email };
}

/**
 * The backend binds the account to the `cm_session` cookie, so the source of
 * truth is GET /api/auth/me — nothing is kept in localStorage.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [sessionVersion, setSessionVersion] = useState(0);

  useEffect(() => {
    getMe()
      .then((me) => setUser(me.authenticated ? toUser(me.email) : null))
      .catch(() => setUser(null));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiLogin(email, password);
    setUser(toUser(me.email));
    setSessionVersion((v) => v + 1);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const me = await apiRegister(email, password);
    setUser(toUser(me.email));
    setSessionVersion((v) => v + 1);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        sessionVersion,
        openLoginModal: () => setIsLoginModalOpen(true),
        closeLoginModal: () => setIsLoginModalOpen(false),
        isLoginModalOpen,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
