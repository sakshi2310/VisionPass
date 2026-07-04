import {
  Bell,
  Building2,
  CalendarCheck2,
  ChartColumnIncreasing,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  DoorOpen,
  LayoutDashboard,
  LogOut,
  ScanFace,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  UserRound,
  Users,
} from "lucide-react";
import { useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  adminNavItems,
  clientNavItems,
  clientUserNavKeys,
  tenantAdminNavItems,
  tenantMemberNavItems,
} from "@/constants/modules";
import { useApp } from "@/context/AppContext";
import { cn } from "@/utils/cn";

const iconMap = {
  LayoutDashboard,
  CalendarCheck2,
  ScanFace,
  Users,
  DoorOpen,
  Sparkles,
  ChartColumnIncreasing,
  ClipboardList,
  Settings2,
  ShieldCheck,
  Building2,
  SlidersHorizontal,
  ChevronDown,
  Bell,
  UserRound,
} as const;

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

function isNavActive(pathname: string, path: string, children?: { path: string }[]) {
  if (children?.length) {
    return children.some((child) => pathname === child.path || pathname.startsWith(`${child.path}/`));
  }
  return pathname === path || pathname.startsWith(`${path}/`);
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, currentTenant, hasModule, logout } = useApp();
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem("visionpass-sidebar-collapsed") === "true");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    () => new Set(["tenant-attendance", "tenant-object-detection", "tenant-cameras"]),
  );

  const visibleItems = (items: typeof tenantAdminNavItems) =>
    items
      .filter((item) => !item.moduleKey || hasModule(item.moduleKey))
      .map((item) => ({
        ...item,
        children: item.children?.filter((child) => !child.moduleKey || hasModule(child.moduleKey)),
      }));

  const navItems =
    user?.role === "SUPER_ADMIN"
      ? adminNavItems
      : user?.role === "TENANT_ADMIN"
        ? visibleItems(tenantAdminNavItems).map((item) => ({
            ...item,
            path: item.path.replace("/client-admin", "/tenant-admin"),
            children: item.children?.map((child) => ({
              ...child,
              path: child.path.replace("/client-admin", "/tenant-admin"),
            })),
          }))
        : user?.role === "CLIENT_ADMIN"
          ? visibleItems(tenantAdminNavItems).map((item) => ({
              ...item,
              path: item.path.replace("/tenant-admin", "/client-admin"),
              children: item.children?.map((child) => ({
                ...child,
                path: child.path.replace("/tenant-admin", "/client-admin"),
              })),
            }))
          : user &&
              [
                "TENANT_USER",
                "CLIENT_USER",
                "SECURITY_GUARD",
                "RECEPTIONIST",
                "ATTENDANCE_OPERATOR",
                "CAMERA_OPERATOR",
                "MANAGER",
              ].includes(user.role)
            ? visibleItems(tenantMemberNavItems)
            : clientNavItems.filter((item) => {
                if (item.adminOnly && user?.role !== "TENANT_ADMIN" && user?.role !== "CLIENT_ADMIN") return false;
                if ((user?.role === "TENANT_USER" || user?.role === "CLIENT_USER") && !clientUserNavKeys.has(item.key)) return false;
                return !item.moduleKey || hasModule(item.moduleKey);
              });

  const roleLabel =
    user?.role === "SUPER_ADMIN"
      ? "Super Admin"
      : user?.role === "TENANT_ADMIN" || user?.role === "CLIENT_ADMIN"
        ? "Client Admin"
        : "Tenant User";

  function toggleCollapsed() {
    setCollapsed((current) => {
      localStorage.setItem("visionpass-sidebar-collapsed", String(!current));
      return !current;
    });
  }

  function toggleGroup(key: string) {
    setExpandedGroups((current) => {
      const next = new Set(current);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-40 w-[290px] border-r border-slate-200 bg-white/95 px-4 py-5 backdrop-blur-xl transition-[transform,width] duration-300 md:static md:translate-x-0 dark:border-white/10 dark:bg-slate-950/90",
        collapsed ? "md:w-[88px]" : "md:w-[290px]",
        open ? "translate-x-0" : "-translate-x-full md:translate-x-0",
      )}
    >
      <div className="flex h-full flex-col gap-5">
        <div className="flex items-center justify-between gap-2">
          <div className={cn(collapsed && "md:hidden")}>
            <BrandWordmark compact />
          </div>
          <button
            type="button"
            onClick={toggleCollapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="hidden rounded-full border border-slate-200 bg-white p-2 text-slate-500 shadow-sm md:inline-flex dark:border-white/10 dark:bg-slate-950"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-white p-2 text-slate-500 shadow-sm md:hidden dark:border-white/10 dark:bg-slate-950"
          >
            <span className="sr-only">Close sidebar</span>
            ×
          </button>
        </div>

        <Card className={cn("p-4 shadow-none", collapsed && "md:hidden")}>
          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Workspace</div>
          <div className="mt-2 text-lg font-semibold">{currentTenant?.name ?? "Platform View"}</div>
          <div className="mt-2"><Badge tone="info">{roleLabel}</Badge></div>
        </Card>

        <nav className="grid gap-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = iconMap[item.icon as keyof typeof iconMap] ?? LayoutDashboard;
            const active = isNavActive(location.pathname, item.path, item.children);

            if (item.children?.length) {
              const expanded = expandedGroups.has(item.key);
              return (
                <div key={item.key} className="grid gap-1">
                  <button
                    type="button"
                    title={collapsed ? item.label : undefined}
                    onClick={() => toggleGroup(item.key)}
                    className={cn(
                      "flex items-center justify-between gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition",
                      active
                        ? "bg-brand-500/10 text-brand-700 shadow-soft dark:text-brand-200"
                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5",
                    )}
                  >
                    <span className="flex items-center gap-3">
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className={cn(collapsed && "md:hidden")}>{item.label}</span>
                    </span>
                    <ChevronDown className={cn("h-4 w-4 transition", expanded && "rotate-180", collapsed && "md:hidden")} />
                  </button>
                  {expanded ? (
                    <div className={cn("ml-4 grid gap-1 border-l border-slate-200 pl-3 dark:border-white/10", collapsed && "md:hidden")}>
                      {item.children.map((child) => {
                        const ChildIcon = iconMap[child.icon as keyof typeof iconMap] ?? LayoutDashboard;
                        return (
                          <NavLink
                            key={child.key}
                            to={child.path}
                            onClick={onClose}
                            className={({ isActive }) =>
                              cn(
                                "flex items-center gap-3 rounded-2xl px-4 py-2 text-sm font-medium transition",
                                isActive
                                  ? "bg-brand-500/10 text-brand-700 shadow-soft dark:text-brand-200"
                                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5",
                              )
                            }
                          >
                            <ChildIcon className="h-4 w-4" />
                            <span>{child.label}</span>
                          </NavLink>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              );
            }

            return (
              <NavLink
                key={item.key}
                to={item.path}
                title={collapsed ? item.label : undefined}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition",
                    isActive
                      ? "bg-brand-500/10 text-brand-700 shadow-soft dark:text-brand-200"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5",
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span className={cn(collapsed && "md:hidden")}>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="mt-auto">
          <Button
            variant="secondary"
            size="md"
            className="w-full"
            leftIcon={<LogOut className="h-4 w-4" />}
            onClick={async () => {
              await logout();
              navigate("/login", { replace: true });
            }}
          >
            <span className={cn(collapsed && "md:hidden")}>Logout</span>
          </Button>
        </div>
      </div>
    </aside>
  );
}
