import { createContext, useContext, useEffect, useState } from "react";

import type { AuthContextType, User, AuthResponse } from "../types/auth";

import { logout, refreshSession } from "../services/auth_service";

import { setAccessToken, clearAccessToken } from "../api/tokenStore";

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);

  const [isInitializing, setIsInitializing] = useState(true);

  // ==========================================
  // Restore session on startup
  // ==========================================

  useEffect(() => {
    let mounted = true;

    async function initializeAuth() {
      try {
        const response = await refreshSession();

        if (!mounted) {
          return;
        }

        setUser(response.user);

        setAccessToken(response.access_token);
      } catch {
        clearAccessToken();

        setUser(null);
      } finally {
        if (mounted) {
          setIsInitializing(false);
        }
      }
    }

    initializeAuth();

    return () => {
      mounted = false;
    };
  }, []);

  function loginUser(data: AuthResponse) {
    setUser(data.user);

    setAccessToken(data.access_token);
  }

  // ==========================================
  // Logout
  // ==========================================

  async function logoutUser() {
    try {
      await logout();
    } catch {
      // ignore
    } finally {
      clearAccessToken();

      setUser(null);
    }
  }

  const value: AuthContextType = {
    user,
    isInitializing,

    setUser,
    loginUser,
    logoutUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
