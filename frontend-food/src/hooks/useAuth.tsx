import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import type { User, LoginPayload, RegisterPayload } from '@/types';
import { authService } from '@/services/auth.service';

/**
 * Session isolation strategy:
 *
 *  - Customer  → localStorage  ('c_token', 'c_user')
 *  - Owner     → sessionStorage ('o_token', 'o_user')
 *
 * Using different storage types means:
 *  - Refreshing any page never mixes the two sessions.
 *  - Opening a new tab always starts a fresh admin session.
 *  - The customer stays logged in across tabs/refreshes normally.
 *  - The owner's session disappears when the browser tab is closed.
 *
 * The shared 'access_token' key (read by the Axios interceptor) is always
 * kept in sync with whichever session is currently active for this page.
 */

const C_TOKEN = 'c_token';
const C_USER = 'c_user';
const O_TOKEN = 'o_token';
const O_USER = 'o_user';
const ACTIVE_TOKEN = 'access_token';
const AUTH_MODE = 'auth_mode';

type AuthMode = 'customer' | 'owner';

// ── Helpers ───────────────────────────────────────────────────────────────────

function readCustomerSession(): User | null {
  try {
    const token = localStorage.getItem(C_TOKEN);
    const stored = localStorage.getItem(C_USER);
    if (token && stored) return JSON.parse(stored) as User;
  } catch {
    localStorage.removeItem(C_TOKEN);
    localStorage.removeItem(C_USER);
  }
  return null;
}

function readOwnerSession(): User | null {
  try {
    const token  = sessionStorage.getItem(O_TOKEN);
    const stored = sessionStorage.getItem(O_USER);
    if (token && stored) return JSON.parse(stored) as User;
  } catch {
    sessionStorage.removeItem(O_TOKEN);
    sessionStorage.removeItem(O_USER);
  }
  return null;
}

function getActiveAuthMode(): AuthMode | null {
  try {
    const mode = localStorage.getItem(AUTH_MODE);
    return mode === 'owner' || mode === 'customer' ? mode : null;
  } catch {
    return null;
  }
}

function setActiveAuthMode(mode: AuthMode) {
  try {
    localStorage.setItem(AUTH_MODE, mode);
  } catch {
    // ignore storage failures
  }
}

function clearActiveAuthMode() {
  try {
    localStorage.removeItem(AUTH_MODE);
  } catch {
    // ignore storage failures
  }
}

function getInitialUser(): User | null {
  const owner = readOwnerSession();
  const customer = readCustomerSession();
  const activeMode = getActiveAuthMode();

  if (window.location.pathname.startsWith('/admin')) {
    if (owner) {
      setActiveAuthMode('owner');
      activateOwnerSession();
    }
    return owner;
  }

  if (activeMode === 'owner' && owner) {
    activateOwnerSession();
    return owner;
  }

  if (customer) {
    setActiveAuthMode('customer');
    activateCustomerSession();
    return customer;
  }

  if (owner) {
    setActiveAuthMode('owner');
    activateOwnerSession();
    return owner;
  }

  return null;
}

function saveOwnerSession(user: User, token: string) {
  sessionStorage.setItem(O_TOKEN, token);
  sessionStorage.setItem(O_USER, JSON.stringify(user));
  localStorage.setItem(ACTIVE_TOKEN, token);
  setActiveAuthMode('owner');
}

function saveCustomerSession(user: User, token: string) {
  localStorage.setItem(C_TOKEN, token);
  localStorage.setItem(C_USER, JSON.stringify(user));
  localStorage.setItem(ACTIVE_TOKEN, token);
  setActiveAuthMode('customer');
}

function activateOwnerSession() {
  const token = sessionStorage.getItem(O_TOKEN);
  if (token) {
    localStorage.setItem(ACTIVE_TOKEN, token);
    setActiveAuthMode('owner');
  }
}

function activateCustomerSession() {
  const token = localStorage.getItem(C_TOKEN);
  if (token) {
    localStorage.setItem(ACTIVE_TOKEN, token);
    setActiveAuthMode('customer');
  }
}

function clearActiveToken() {
  localStorage.removeItem(ACTIVE_TOKEN);
}

function clearOwnerSession() {
  sessionStorage.removeItem(O_TOKEN);
  sessionStorage.removeItem(O_USER);
  clearActiveToken();
  clearActiveAuthMode();
}

function clearCustomerSession() {
  localStorage.removeItem(C_TOKEN);
  localStorage.removeItem(C_USER);
  clearActiveToken();
  clearActiveAuthMode();
}

// ── Context ───────────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isOwner: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  setUser: (user: User | null) => void;
  switchToOwnerStore: () => void;
  /** Used by AdminLoginPage to commit a verified owner session */
  setOwnerSession: (user: User, token: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [user, setUserState] = useState<User | null>(getInitialUser);

  // Auth is resolved synchronously — no async loading needed
  const isLoading = false;

  /** Customer login */
  const login = useCallback(async (payload: LoginPayload) => {
    const result = await authService.login(payload);
    saveCustomerSession(result.user, result.access_token);
    if (result.user.is_owner) {
      saveOwnerSession(result.user, result.access_token);
    }
    setUserState(result.user);
  }, []);

  /** Customer registration */
  const register = useCallback(async (payload: RegisterPayload) => {
    const result = await authService.register(payload);
    saveCustomerSession(result.user, result.access_token);
    setUserState(result.user);
  }, []);

  useEffect(() => {
    if (location.pathname.startsWith('/admin')) {
      activateOwnerSession();
      return;
    }

    const mode = getActiveAuthMode();
    if (mode === 'owner') {
      activateOwnerSession();
      return;
    }

    activateCustomerSession();
  }, [location.pathname]);

  const switchToOwnerStore = useCallback(() => {
    const owner = readOwnerSession();
    if (!owner) return;
    activateOwnerSession();
    setUserState(owner);
  }, []);

  /** Logout — clears the right session based on who is logged in */
  const logout = useCallback(() => {
    if (user?.is_owner) {
      clearOwnerSession();
    } else {
      clearCustomerSession();
    }
    setUserState(null);
  }, [user]);

  const setUser = useCallback((u: User | null) => {
    setUserState(u);
  }, []);

  /**
   * Called by AdminLoginPage ONLY after confirming the user is the owner.
   * Writes to sessionStorage so it never touches the customer localStorage.
   */
  const setOwnerSession = useCallback((u: User, token: string) => {
    saveOwnerSession(u, token);
    setUserState(u);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isOwner: !!user?.is_owner,
        isLoading,
        login,
        register,
        logout,
        setUser,
        switchToOwnerStore,
        setOwnerSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
