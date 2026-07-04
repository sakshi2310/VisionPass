import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  clearSession,
  changePassword as changePasswordRequest,
  checkBootstrapStatus,
  getCurrentSession,
  loadStoredAccessToken,
  loadStoredTenantId,
  loadStoredTenants,
  loadStoredTheme,
  login as loginRequest,
  logout as logoutRequest,
  saveStoredTenantId,
  saveStoredTenants,
  saveStoredTheme,
  saveStoredUser,
  signup as signupRequest,
} from "@/services/auth";
import { adminApi } from "@/services/admin";
import { clearStoredUserModuleKeys, getUserWorkspaceDashboard, loadStoredUserModuleKeys } from "@/services/userWorkspace";
import type { FeatureRule, ModuleKey, Tenant, ThemeMode, User } from "@/types";

type AppContextValue = {
  authReady: boolean;
  user: User | null;
  theme: ThemeMode;
  tenants: Tenant[];
  featureRules: FeatureRule[];
  currentTenant: Tenant | null;
  login: (email: string, password: string) => Promise<User>;
  signup: (fullName: string, email: string, organizationName: string, password: string) => Promise<User>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<User>;
  logout: () => Promise<void>;
  setTheme: (theme: ThemeMode) => void;
  setCurrentTenantId: (tenantId: string) => void;
  toggleTenantModule: (tenantId: string, moduleKey: ModuleKey, enabled: boolean) => void;
  updateTenant: (tenantId: string, patch: Partial<Tenant>) => void;
  createRule: (rule: Omit<FeatureRule, "id" | "createdAt" | "updatedAt">) => FeatureRule;
  updateRule: (ruleId: string, patch: Partial<FeatureRule>) => void;
  hasModule: (moduleKey: ModuleKey) => boolean;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setThemeState] = useState<ThemeMode>(() => loadStoredTheme());
  const [tenants, setTenants] = useState<Tenant[]>(() => loadStoredTenants([]));
  const [authReady, setAuthReady] = useState(false);
  const [featureRules, setFeatureRules] = useState<FeatureRule[]>(() => {
    if (typeof window === "undefined") return [];
    const raw = localStorage.getItem("visionpass-feature-rules");
    return raw ? (JSON.parse(raw) as FeatureRule[]) : [];
  });
  const [userModuleKeys, setUserModuleKeys] = useState<string[]>(() => loadStoredUserModuleKeys());
  const [currentTenantId, setCurrentTenantIdState] = useState<string>(() => {
    return loadStoredTenantId() ?? "";
  });

  async function loadAdminTenants() {
    try {
      const remoteTenants = await adminApi.listTenants();
      setTenants(remoteTenants as Tenant[]);
      if (remoteTenants.length > 0 && !remoteTenants.some((tenant) => tenant.id === currentTenantId)) {
        setCurrentTenantIdState(remoteTenants[0].id);
      }
    } catch {
      // Fall back to local seed tenants if the admin API is not available yet.
    }
  }

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    document.documentElement.dataset.theme = theme;
    saveStoredTheme(theme);
  }, [theme]);

  useEffect(() => {
    saveStoredUser(user);
  }, [user]);

  useEffect(() => {
    saveStoredTenants(tenants);
  }, [tenants]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("visionpass-feature-rules", JSON.stringify(featureRules));
    }
  }, [featureRules]);

  useEffect(() => {
    saveStoredTenantId(currentTenantId);
  }, [currentTenantId]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrapSession() {
      try {
        const required = await checkBootstrapStatus();
        void required;
      } catch {
        // Ignore bootstrap status failures and continue with local session bootstrap.
      }

      if (!loadStoredAccessToken()) {
        clearSession();
        if (!cancelled) {
          setUser(null);
          setAuthReady(true);
        }
        return;
      }

      const currentSession = await getCurrentSession();
      if (cancelled) return;

      const currentUser = currentSession?.user ?? null;
      setUser(currentUser);
      if (currentUser) {
        setCurrentTenantIdState(currentUser.tenantId || "");
        if (currentUser.role === "SUPER_ADMIN") {
          await loadAdminTenants();
        } else if (currentSession?.tenant) {
          setTenants((current) => {
            const nextTenant = currentSession.tenant as Tenant;
            const filtered = current.filter((tenant) => tenant.id !== nextTenant.id);
            return [nextTenant, ...filtered];
          });
          setCurrentTenantIdState(currentSession.tenant.id);
        }
      }
      setAuthReady(true);
    }

    void bootstrapSession();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (user && !tenants.some((tenant) => tenant.id === currentTenantId)) {
      setCurrentTenantIdState(user.tenantId || "");
    }
  }, [currentTenantId, tenants, user]);

  useEffect(() => {
    if (!user || user.role !== "SUPER_ADMIN") return;

    const handleTenantChange = () => {
      void loadAdminTenants();
    };

    window.addEventListener("visionpass-admin-tenants-changed", handleTenantChange);
    return () => {
      window.removeEventListener("visionpass-admin-tenants-changed", handleTenantChange);
    };
  }, [currentTenantId, user]);

  useEffect(() => {
    let cancelled = false;

    async function syncUserModules() {
      if (!user) {
        clearStoredUserModuleKeys();
        if (!cancelled) {
          setUserModuleKeys([]);
        }
        return;
      }

      if (user.role !== "TENANT_USER") {
        clearStoredUserModuleKeys();
        if (!cancelled) {
          setUserModuleKeys([]);
        }
        return;
      }

      try {
        const dashboard = await getUserWorkspaceDashboard();
        if (cancelled) return;
        const moduleKeys = dashboard.features
          .map((feature) => feature.module_key ?? feature.feature_code)
          .filter((moduleKey): moduleKey is string => Boolean(moduleKey));
        setUserModuleKeys(moduleKeys);
      } catch {
        if (!cancelled) {
          setUserModuleKeys(loadStoredUserModuleKeys());
        }
      }
    }

    void syncUserModules();

    return () => {
      cancelled = true;
    };
  }, [user?.id, user?.role]);

  const currentTenant =
    tenants.find((tenant) => tenant.id === currentTenantId) ??
    (user ? tenants.find((tenant) => tenant.id === user.tenantId) ?? null : null);

  const value = useMemo<AppContextValue>(
    () => ({
      authReady,
      user,
      theme,
      tenants,
      featureRules,
      currentTenant,
      login: async (email, password) => {
        const session = await loginRequest(email, password);
        setUser(session.user);
        setCurrentTenantIdState(session.user.tenantId || "");
        if (session.user.role === "SUPER_ADMIN") {
          try {
            await loadAdminTenants();
          } catch {
            // Keep the local tenant cache.
          }
        } else if (session.tenant) {
          setTenants((current) => {
            const nextTenant = session.tenant as Tenant;
            const filtered = current.filter((tenant) => tenant.id !== nextTenant.id);
            return [nextTenant, ...filtered];
          });
          setCurrentTenantIdState(session.tenant.id);
        }
        return session.user;
      },
      signup: async (fullName, email, organizationName, password) => {
        const session = await signupRequest(fullName, email, organizationName, password);
        setUser(session.user);
        setCurrentTenantIdState(session.user.tenantId || "");
        if (session.user.role === "SUPER_ADMIN") {
          try {
            await loadAdminTenants();
          } catch {
            // Keep the local tenant cache.
          }
        } else if (session.tenant) {
          setTenants((current) => {
            const nextTenant = session.tenant as Tenant;
            const filtered = current.filter((tenant) => tenant.id !== nextTenant.id);
            return [nextTenant, ...filtered];
          });
          setCurrentTenantIdState(session.tenant.id);
        }
        return session.user;
      },
      changePassword: async (currentPassword, newPassword) => {
        const updatedUser = await changePasswordRequest(currentPassword, newPassword);
        setUser(updatedUser);
        return updatedUser;
      },
      logout: async () => {
        await logoutRequest();
        setUser(null);
        setTenants([]);
        setCurrentTenantIdState("");
        setUserModuleKeys([]);
        clearStoredUserModuleKeys();
      },
      setTheme: setThemeState,
      setCurrentTenantId: setCurrentTenantIdState,
      toggleTenantModule: (tenantId, moduleKey, enabled) => {
        setTenants((prev) =>
          prev.map((tenant) =>
            tenant.id === tenantId
              ? {
                  ...tenant,
                  enabledModules: enabled
                    ? Array.from(new Set([...tenant.enabledModules, moduleKey]))
                    : tenant.enabledModules.filter((module) => module !== moduleKey),
                }
              : tenant,
          ),
        );
      },
      updateTenant: (tenantId, patch) => {
        setTenants((prev) => prev.map((tenant) => (tenant.id === tenantId ? { ...tenant, ...patch } : tenant)));
      },
      createRule: (rule) => {
        const date = new Date().toISOString().slice(0, 10);
        const nextRule: FeatureRule = {
          ...rule,
          id: `rule-${crypto.randomUUID().slice(0, 8)}`,
          createdAt: date,
          updatedAt: date,
        };
        setFeatureRules((prev) => [nextRule, ...prev]);
        return nextRule;
      },
      updateRule: (ruleId, patch) => {
        setFeatureRules((prev) =>
          prev.map((rule) =>
            rule.id === ruleId ? { ...rule, ...patch, updatedAt: new Date().toISOString().slice(0, 10) } : rule,
          ),
        );
      },
      hasModule: (moduleKey) => {
        const commonModules = new Set(["camera_management", "live_feed", "reports"]);
        if (commonModules.has(moduleKey)) return true;
        if (!currentTenant) return false;
        if (user?.role === "TENANT_USER") {
          return userModuleKeys.includes(moduleKey);
        }
        return currentTenant.enabledModules.includes(moduleKey);
      },
    }),
    [authReady, currentTenant, featureRules, tenants, theme, user, userModuleKeys],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within AppProvider");
  }
  return context;
}
