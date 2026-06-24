import {
  Building2,
  CalendarCheck2,
  ChartColumnIncreasing,
  ClipboardList,
  DoorOpen,
  LayoutDashboard,
  LogOut,
  ScanFace,
  Settings2,
  ShieldCheck,
  Sparkles,
  SlidersHorizontal,
  Users,
} from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';

import { BrandWordmark } from '@/components/brand/BrandWordmark';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { adminNavItems, clientNavItems, clientUserNavKeys, tenantAdminNavItems, tenantMemberNavItems } from '@/constants/modules';
import { useApp } from '@/context/AppContext';
import { cn } from '@/utils/cn';

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
} as const;

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: SidebarProps) {
  const navigate = useNavigate();
  const { user, currentTenant, hasModule, logout } = useApp();

  const navItems =
    user?.role === 'SUPER_ADMIN'
      ? adminNavItems
      : user?.role === 'TENANT_ADMIN'
        ? tenantAdminNavItems
        : user?.role === 'TENANT_USER'
          ? tenantMemberNavItems
          : clientNavItems.filter((item) => {
              if (item.adminOnly && user?.role !== 'TENANT_ADMIN' && user?.role !== 'CLIENT_ADMIN') return false;
              if ((user?.role === 'TENANT_USER' || user?.role === 'CLIENT_USER') && !clientUserNavKeys.has(item.key)) return false;
              return !item.moduleKey || hasModule(item.moduleKey);
            });

  const roleLabel =
    user?.role === 'SUPER_ADMIN'
      ? 'Super Admin'
      : user?.role === 'TENANT_ADMIN'
        ? 'Tenant Admin'
        : 'Tenant User';

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 w-[290px] border-r border-slate-200 bg-white/95 px-4 py-5 backdrop-blur-xl transition-transform duration-300 md:static md:translate-x-0 dark:border-white/10 dark:bg-slate-950/90',
        open ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
      )}
    >
      <div className="flex h-full flex-col gap-5">
        <div className="flex items-center justify-between">
          <BrandWordmark compact />
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-slate-200 bg-white p-2 text-slate-500 shadow-sm md:hidden dark:border-white/10 dark:bg-slate-950 dark:text-slate-400"
          >
            <span className="sr-only">Close sidebar</span>
            x
          </button>
        </div>

        <Card className="p-4 shadow-none">
          <div className="text-xs uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Workspace</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{currentTenant?.name ?? 'Platform View'}</div>
          <div className="mt-2 flex items-center gap-2">
            <Badge tone="info">{roleLabel}</Badge>
          </div>
        </Card>

        <nav className="grid gap-1">
          {navItems.map((item) => {
            const Icon = iconMap[item.icon as keyof typeof iconMap] ?? LayoutDashboard;
            return (
              <NavLink
                key={item.key}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition',
                    isActive
                      ? 'bg-brand-500/10 text-brand-700 shadow-soft dark:text-brand-200'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white',
                  )
                }
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
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
              const role = user?.role;
              await logout();
              navigate(role === 'SUPER_ADMIN' ? '/admin/login' : '/login', { replace: true });
            }}
          >
            Logout
          </Button>
        </div>
      </div>
    </aside>
  );
}
