import Link from "next/link";

import { BrandMark } from "@/components/brand-mark";

export default function HomePage() {
  return (
    <main className="home-page">
      <header className="home-topbar">
        <div className="brand-row">
          <BrandMark />
          <div>
            <div className="brand-name">VisionPass AI</div>
            <div className="brand-tag">Centralized AI gate platform</div>
          </div>
        </div>
        <div className="home-topbar-links">
          <Link className="text-link" href="/login">
            Login
          </Link>
          <Link className="button button-compact" href="/tenant/login">
            Tenant login
          </Link>
        </div>
      </header>

      <section className="hero-grid">
        <div className="hero-copy">
          <div className="eyebrow">Multi-tenant access intelligence</div>
          <h1>One platform for attendance, visitors, access, and alerts.</h1>
          <p>
            VisionPass AI gives each tenant a controlled dashboard with only the modules enabled for
            their plan, while super-admins keep full visibility across the platform.
          </p>
          <div className="hero-actions">
            <Link className="button" href="/bootstrap">
              Start tenant setup
            </Link>
            <Link className="button secondary" href="/login">
              Sign in
            </Link>
          </div>
          <div className="hero-metrics">
            <div className="metric-card">
              <span>1</span>
              <label>shared codebase</label>
            </div>
            <div className="metric-card">
              <span>9</span>
              <label>toggleable modules</label>
            </div>
            <div className="metric-card">
              <span>100%</span>
              <label>tenant-scoped views</label>
            </div>
          </div>
        </div>

        <aside className="hero-panel">
          <div className="hero-panel-title">Product snapshot</div>
          <div className="hero-panel-list">
            <div>
              <strong>Attendance</strong>
              <span>Check-ins and summaries</span>
            </div>
            <div>
              <strong>Visitor flow</strong>
              <span>Classify unknown faces</span>
            </div>
            <div>
              <strong>Access control</strong>
              <span>Grant, deny, or review</span>
            </div>
            <div>
              <strong>AI assistant</strong>
              <span>Ask about logs in plain language</span>
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
