import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { setAuthToken } from "./api/client";
import { login as apiLogin, me as apiMe } from "./api/paeos";

interface Session {
  token: string;
  tenantSlug: string;
  email: string;
  permissions: string[];
}

interface AuthState {
  session: Session | null;
  signIn: (tenant: string, email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const STORAGE_KEY = "paeos.session";

function load(): Session | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw) as Session;
    setAuthToken(s.token);
    return s;
  } catch {
    return null;
  }
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(load);

  const signIn = useCallback(
    async (tenant: string, email: string, password: string) => {
      const { access_token } = await apiLogin(tenant, email, password);
      setAuthToken(access_token);
      let permissions: string[] = [];
      try {
        permissions = (await apiMe()).permissions;
      } catch {
        permissions = [];
      }
      const next: Session = { token: access_token, tenantSlug: tenant, email, permissions };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* ignore storage failures */
      }
      setSession(next);
    },
    [],
  );

  const signOut = useCallback(() => {
    setAuthToken(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setSession(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ session, signIn, signOut }),
    [session, signIn, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
