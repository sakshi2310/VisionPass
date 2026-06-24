import Link from "next/link";
import type { ReactNode } from "react";

import { BrandMark } from "@/components/brand-mark";

type AppShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
};

export function AppShell({ title, subtitle, children }: AppShellProps) {
  return (
    <main className="app-shell">
      <section className="app-shell-panel">
        <div className="brand-row">
          <BrandMark />
          <div>
            <div className="brand-name">VisionPass AI</div>
            <div className="brand-tag">Centralized gate intelligence</div>
          </div>
        </div>

        <div className="app-shell-copy">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>

        <div className="feature-list">
          <div className="feature-pill">Attendance</div>
          <div className="feature-pill">Visitors</div>
          <div className="feature-pill">Access control</div>
          <div className="feature-pill">Alerts</div>
        </div>

        <div className="app-shell-footer">
          <Link href="/" className="text-link">
            Back to home
          </Link>
        </div>
      </section>

      <section className="app-shell-form">{children}</section>
    </main>
  );
}
