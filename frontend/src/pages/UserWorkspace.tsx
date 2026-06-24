import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useApp } from "@/context/AppContext";

type UserWorkspaceProps = {
  title: string;
  description: string;
  routeLabel: string;
};

function UserWorkspace({ title, description, routeLabel }: UserWorkspaceProps) {
  const { user } = useApp();
  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">{routeLabel}</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">{description}</p>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Signed in as</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{user?.name ?? "Tenant User"}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Role</div>
          <div className="mt-2"><Badge tone="info">{user?.role ?? "TENANT_USER"}</Badge></div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tenant</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{user?.tenantId ?? "-"}</div>
        </Card>
      </div>
    </div>
  );
}

export function UserDashboard() {
  return (
    <UserWorkspace
      routeLabel="User Dashboard"
      title="Tenant user dashboard"
      description="A lightweight landing area for tenant users after login."
    />
  );
}

export function UserSecurity() {
  return <UserWorkspace routeLabel="Security" title="Security guard console" description="Assigned security operations and live checks belong here." />;
}

export function UserReception() {
  return <UserWorkspace routeLabel="Reception" title="Reception desk console" description="Reception workflow and visitor handoffs belong here." />;
}

export function UserAttendance() {
  return <UserWorkspace routeLabel="Attendance" title="Attendance operator console" description="Attendance review and correction tools belong here." />;
}

export function UserCameras() {
  return <UserWorkspace routeLabel="Cameras" title="Camera operator console" description="Camera views and device controls belong here." />;
}

export function UserSettings() {
  return <UserWorkspace routeLabel="Settings" title="Tenant user settings" description="Profile and security preferences for tenant users live here." />;
}
