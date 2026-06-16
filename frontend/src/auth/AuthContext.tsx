import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, tokenStore } from "../api/client";

interface User {
  id: number;
  username: string;
  email: string;
  roles: string[];
  permissions: string[];
  is_superuser: boolean;
}

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  can: (perm: string) => boolean;
  isAdmin: boolean;
}

const Ctx = createContext<AuthCtx>(null as never);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStore.access) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me/")
      .then((r) => setUser(r.data))
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  async function login(username: string, password: string) {
    const { data } = await api.post("/auth/login/", { username, password });
    tokenStore.set(data.access, data.refresh);
    setUser(data.user);
  }

  function logout() {
    tokenStore.clear();
    setUser(null);
    window.location.href = "/login";
  }

  function can(perm: string) {
    if (!user) return false;
    return user.is_superuser || user.permissions.includes("*") || user.permissions.includes(perm);
  }

  const isAdmin = !!user && (user.is_superuser || user.roles.includes("Super Admin"));

  return (
    <Ctx.Provider value={{ user, loading, login, logout, can, isAdmin }}>{children}</Ctx.Provider>
  );
}

export const useAuth = () => useContext(Ctx);
