"use client";

import { useEffect, useState } from "react";

import { BrandMark } from "@/components/brand-mark";

type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string | null;
  is_active: boolean;
  created_at: string;
};

type Tenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  plan: string;
  created_at: string;
  updated_at: string;
};

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("visionpass_user");
    const storedTenant = localStorage.getItem("visionpass_seed_tenant");
    if (storedUser) setUser(JSON.parse(storedUser) as User);
    if (storedTenant) setTenant(JSON.parse(storedTenant) as Tenant);
  }, []);

  return (
    <main className="dashboard">
      <header className="dashboard-topbar">
        <div className="brand-row">
          <BrandMark />
          <div>
            <div className="brand-name">VisionPass AI</div>
            <div className="brand-tag">Tenant dashboard</div>
          </div>
        </div>
        <div className="dashboard-status">Live workspace</div>
      </header>

      <section className="dashboard-hero">
        <div>
          <div className="eyebrow">Operational overview</div>
          <h1>Welcome to the centralized control room.</h1>
          <p>
            This shell is ready for module-by-module expansion: attendance, employees, cameras,
            visitors, access, alerts, analytics, and AI assistant.
          </p>
        </div>
        <div className="dashboard-chip-row">
          <div className="dashboard-chip">Attendance ready</div>
          <div className="dashboard-chip">Module flags live</div>
          <div className="dashboard-chip">Tenant isolated</div>
        </div>
      </section>

      <section className="grid">
        <article className="card stat-card">
          <span>Current user</span>
          <pre>{JSON.stringify(user, null, 2)}</pre>
        </article>
        <article className="card stat-card">
          <span>Tenant</span>
          <pre>{JSON.stringify(tenant, null, 2)}</pre>
        </article>
        <article className="card stat-card">
          <span>Next module</span>
          <p>Feature flags and admin toggles</p>
        </article>
      </section>
    </main>
  );
}
