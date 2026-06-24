# Centralized AI Gate Product Plan
conda activate "D:\Vision pass\backend\venv"

## 1. Better Project Name Options

Top recommendation: **VisionPass AI**

Why: it sounds like a complete product, not only a gate project. It can cover attendance, access control, visitor intelligence, alerts, analytics, and GenAI queries under one brand.

Other strong names:

1. **VisionPass AI** — smart, product-ready, easy to remember.
2. **VisionPass** — good for face-based access and attendance.
3. **TenantGate AI** — clearly communicates multi-tenant centralized control.
4. **AccessIQ** — professional and enterprise-style.
5. **FaceGate Cloud** — direct and easy to understand.
6. **SecureEntry AI** — security-focused.
7. **EntryVision** — clean name for vision-based entry systems.
8. **OptiGate AI** — modern and flexible.
9. **NexaGate** — startup-style brand name.
10. **GateOps AI** — good if the product is positioned as an operations platform.

Recommended final product name: **VisionPass AI**

Suggested tagline: **Centralized AI-powered attendance, visitor, and access intelligence for multi-tenant organizations.**

---

## 2. Analysis of the Existing Claude Plan

The existing plan is directionally good. The best idea in it is the **single shared codebase with tenant-based feature flags**, because that is what makes the project look like a real SaaS product instead of three separate custom projects.

### What is strong

- Correct architecture choice: one backend, one frontend, one database, many tenants.
- Feature flags are placed at the center of the product.
- The admin panel controls tenant modules centrally.
- The client dashboard dynamically renders only enabled modules.
- PostgreSQL + FastAPI + Next.js is a strong stack for this product.
- The 3-tenant demo idea is excellent for interviews and product pitching.

### What needs improvement

The original plan is too compressed for a production-grade end-to-end product. A 20-day build is possible for a demo, but not for a stable product unless the scope is controlled very tightly.

Missing or underdefined areas:

- Clear product naming and positioning.
- Database schema details.
- Auth and role model.
- Tenant isolation rules.
- Camera stream strategy.
- Face embedding storage and security.
- Audit logs.
- Device/camera management.
- Deployment environments.
- API route contract.
- Error handling and observability.
- Testing strategy.
- Privacy and biometric-data security.
- Demo strategy and phased launch.

### Corrected planning assumption

For a strong placement/interview demo: **4-6 weeks** is realistic.

For a more polished end-to-end product: **8-10 weeks** is better.

---

## 3. Final Product Vision

**VisionPass AI** is a centralized multi-tenant AI access and attendance platform. A super-admin can create client organizations, assign modules through feature flags, manage users, view usage, and control product access. Each client logs in to a dashboard that only shows the modules enabled for that tenant.

The product uses phone/IP camera streams for video input, a Python AI engine for face detection/recognition/liveness, FastAPI for backend APIs, PostgreSQL for multi-tenant storage, and Next.js/React for dashboards.

---

## 4. Final Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js + React + TypeScript | Client dashboard and admin panel |
| UI | Tailwind CSS + shadcn/ui | Clean professional interface |
| Charts | Recharts | Attendance, alerts, analytics charts |
| Backend | FastAPI + Python | API, AI orchestration, tenant logic |
| Database | PostgreSQL | Multi-tenant persistent storage |
| ORM | SQLAlchemy 2.0 | Database models and queries |
| Migrations | Alembic | Versioned database schema changes |
| Auth | JWT or Supabase Auth | Login, sessions, roles |
| AI/CV | OpenCV + MediaPipe/YuNet + ONNX Runtime | Face detection, liveness, recognition |
| Model Training | Google Colab GPU | Train/fine-tune liveness model |
| Background Jobs | Celery/RQ or APScheduler | Alerts, reports, periodic cleanup |
| Cache/Queue | Redis | Optional for scalable events and jobs |
| Storage | S3/Supabase Storage/local volume | Face snapshots, logs, exports |
| Deployment | Vercel + Render/Railway/Fly.io | Frontend + backend hosting |
| Monitoring | Sentry + structured logs | Debugging and production visibility |

---

## 5. Centralized Multi-Tenant Architecture

### Main principle

There is only **one shared codebase** and one platform. Tenants are separated by `tenant_id`, roles, and feature flags.

### Tenant isolation rules

Every business table must include `tenant_id` unless it is truly global.

Examples:

- `employees.tenant_id`
- `attendance_logs.tenant_id`
- `visitors.tenant_id`
- `alerts.tenant_id`
- `devices.tenant_id`
- `feature_flags.tenant_id`

Every API request must resolve:

1. Current authenticated user.
2. User role.
3. Tenant context.
4. Enabled module list.
5. Whether the requested operation is allowed.

### Access model

| Role | Scope | Capabilities |
|---|---|---|
| Super Admin | All tenants | Create tenants, enable modules, view platform analytics |
| Tenant Admin | Own tenant | Manage employees, cameras, reports, settings |
| Operator/Security | Own tenant | View live recognition, alerts, visitors |
| Viewer | Own tenant | Read-only dashboards and reports |

---

## 6. Core Modules

### Always-on core modules

1. **Tenant Context Module**
   - Resolves tenant from JWT/session.
   - Blocks cross-tenant data access.
   - Adds tenant filters to database queries.

2. **Camera Input Module**
   - Supports phone IP Webcam stream.
   - Supports RTSP/IP camera URLs.
   - Stores camera/device records per tenant.

3. **Face Detection Module**
   - Uses CPU-friendly detector such as MediaPipe or YuNet.
   - Finds faces from frames.
   - Rejects low-quality frames.

4. **Face Embedding Module**
   - Generates face embeddings.
   - Compares embeddings against tenant-specific employees.
   - Uses configurable threshold.

5. **Liveness Module**
   - Starts simple: blink/head movement/challenge-based checks.
   - Later: Colab-trained liveness model exported to ONNX.
   - Runs ONNX inference on CPU in production.

6. **Audit Log Module**
   - Records sensitive actions.
   - Examples: module toggled, employee enrolled, access granted, user login.

---

## 7. Toggleable Client Modules

| Module | Feature Flag Key | Description |
|---|---|---|
| Attendance | `attendance` | Check-in/check-out logs and reports |
| Visitor Classification | `visitor_classification` | Known staff vs unknown visitor detection |
| Access Control | `access_control` | Gate/door decision logic |
| Alerts | `alerts` | Unknown person, after-hours, repeated failure alerts |
| Anomaly Detection | `anomaly_detection` | Loitering, tailgating, unusual access patterns |
| GenAI Assistant | `genai_assistant` | Natural-language log and report queries |
| Analytics | `analytics` | Charts, exports, summaries |
| Camera Management | `camera_management` | Add/edit camera streams |
| Usage Billing | `usage_billing` | Per-tenant usage counts for admin |

Every module must be checked in two places:

1. **Backend**: API route blocks disabled modules.
2. **Frontend**: UI hides disabled modules.

Frontend hiding is not security. Backend checks are mandatory.

---

## 8. Database Schema

### `tenants`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Tenant ID |
| name | varchar | Client/company name |
| slug | varchar unique | URL-safe identifier |
| status | varchar | active/suspended/trial |
| plan | varchar | basic/pro/premium |
| created_at | timestamptz | Created timestamp |
| updated_at | timestamptz | Updated timestamp |

### `users`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | User ID |
| tenant_id | UUID nullable | Null for super-admin |
| email | varchar unique | Login email |
| password_hash | text | If using internal auth |
| full_name | varchar | User name |
| role | varchar | super_admin/tenant_admin/operator/viewer |
| is_active | boolean | Account status |
| created_at | timestamptz | Created timestamp |

### `feature_flags`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Flag ID |
| tenant_id | UUID FK | Client tenant |
| module_name | varchar | Example: attendance |
| enabled | boolean | On/off |
| config | jsonb | Module-specific settings |
| updated_by | UUID FK | Admin who changed it |
| updated_at | timestamptz | Timestamp |

Unique index: `(tenant_id, module_name)`

### `employees`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Employee ID |
| tenant_id | UUID FK | Tenant owner |
| employee_code | varchar | Client-specific code |
| full_name | varchar | Employee name |
| department | varchar | Optional |
| designation | varchar | Optional |
| status | varchar | active/inactive |
| face_embedding | vector/jsonb/bytea | Encrypted or protected embedding |
| face_image_url | text | Optional reference image |
| created_at | timestamptz | Timestamp |

Recommended: use `pgvector` later for scalable vector search. Start with `jsonb` or `bytea` for MVP.

### `cameras`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Camera ID |
| tenant_id | UUID FK | Tenant owner |
| name | varchar | Gate 1, Reception, Main Door |
| stream_url | text | IP Webcam/RTSP URL |
| location | varchar | Physical location |
| is_active | boolean | Active/inactive |
| created_at | timestamptz | Timestamp |

### `attendance_logs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Log ID |
| tenant_id | UUID FK | Tenant owner |
| employee_id | UUID FK | Employee |
| camera_id | UUID FK | Camera used |
| event_type | varchar | check_in/check_out |
| confidence | numeric | Recognition confidence |
| captured_image_url | text | Optional snapshot |
| occurred_at | timestamptz | Event time |

### `visitor_logs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Visitor event ID |
| tenant_id | UUID FK | Tenant owner |
| camera_id | UUID FK | Camera used |
| classification | varchar | unknown/known/visitor |
| confidence | numeric | Model confidence |
| snapshot_url | text | Optional snapshot |
| occurred_at | timestamptz | Event time |

### `access_events`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Access event ID |
| tenant_id | UUID FK | Tenant owner |
| employee_id | UUID nullable | Known employee if matched |
| camera_id | UUID FK | Camera/device |
| decision | varchar | granted/denied/manual_review |
| reason | text | Why decision happened |
| confidence | numeric | Recognition confidence |
| occurred_at | timestamptz | Event time |

### `alerts`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Alert ID |
| tenant_id | UUID FK | Tenant owner |
| alert_type | varchar | unknown_person/after_hours/tailgating |
| severity | varchar | low/medium/high/critical |
| title | varchar | Alert title |
| message | text | Alert details |
| status | varchar | open/acknowledged/resolved |
| metadata | jsonb | Extra data |
| created_at | timestamptz | Timestamp |

### `audit_logs`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | Audit ID |
| tenant_id | UUID nullable | Null for global admin actions |
| actor_user_id | UUID FK | User who acted |
| action | varchar | feature_flag.updated, employee.enrolled |
| resource_type | varchar | tenant/user/employee/module |
| resource_id | UUID nullable | Target record |
| metadata | jsonb | Before/after values |
| created_at | timestamptz | Timestamp |

---

## 9. Backend API Structure

Base URL: `/api/v1`

### Auth

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/refresh`

### Super Admin

- `POST /admin/tenants`
- `GET /admin/tenants`
- `GET /admin/tenants/{tenant_id}`
- `PATCH /admin/tenants/{tenant_id}`
- `GET /admin/tenants/{tenant_id}/modules`
- `PATCH /admin/tenants/{tenant_id}/modules/{module_name}`
- `GET /admin/analytics/overview`

### Tenant Modules

- `GET /tenant/modules`
- `GET /tenant/settings`
- `PATCH /tenant/settings`

### Employees / Enrollment

- `POST /employees`
- `GET /employees`
- `GET /employees/{employee_id}`
- `PATCH /employees/{employee_id}`
- `DELETE /employees/{employee_id}`
- `POST /employees/{employee_id}/enroll-face`

### Recognition

- `POST /recognition/frame`
- `POST /recognition/stream-event`

### Attendance

- `POST /attendance/check`
- `GET /attendance/logs`
- `GET /attendance/summary`
- `GET /attendance/export`

### Visitors

- `GET /visitors/logs`
- `PATCH /visitors/{visitor_id}/classify`

### Access Control

- `POST /access/decision`
- `GET /access/events`

### Alerts

- `GET /alerts`
- `PATCH /alerts/{alert_id}/acknowledge`
- `PATCH /alerts/{alert_id}/resolve`

### Cameras

- `POST /cameras`
- `GET /cameras`
- `PATCH /cameras/{camera_id}`
- `DELETE /cameras/{camera_id}`
- `POST /cameras/{camera_id}/test-stream`

### GenAI Assistant

- `POST /assistant/query`
- `GET /assistant/history`

---

## 10. Backend Enforcement Pattern

Every protected route should use dependencies like this:

```python
current_user = Depends(get_current_user)
tenant = Depends(get_current_tenant)
require_module("attendance")
require_role(["tenant_admin", "operator"])
```

Every database query should include tenant filtering:

```python
select(AttendanceLog).where(
    AttendanceLog.tenant_id == current_user.tenant_id
)
```

Super-admin routes are the only routes allowed to query across tenants.

---

## 11. AI Pipeline

### Phase 1: MVP recognition pipeline

1. Receive frame from phone/IP camera.
2. Detect face.
3. Validate image quality.
4. Generate embedding.
5. Compare only against employees from the same tenant.
6. Return match/no-match with confidence.
7. Create attendance/access/visitor event depending on enabled modules.

### Phase 2: Better liveness

Start with low-complexity methods:

- Blink detection.
- Head movement challenge.
- Multiple-frame consistency.
- Face-size and quality checks.

Then add model-based liveness:

- Train/fine-tune on Colab GPU.
- Export to ONNX.
- Run with ONNX Runtime on CPU.

### Phase 3: Performance improvement

- Cache tenant employee embeddings in memory.
- Refresh cache when employee enrollment changes.
- Use pgvector when employee count grows.
- Process video frames at intervals instead of every frame.
- Add background workers for heavy tasks.

---

## 12. Frontend Product Structure

### Super Admin Dashboard

Screens:

1. Login
2. Platform overview
3. Tenant list
4. Create/edit tenant
5. Feature module toggle page
6. Usage analytics
7. Audit log
8. Billing/plan overview

### Client Dashboard

Screens are dynamically rendered based on enabled modules:

1. Home overview
2. Attendance
3. Employees
4. Cameras
5. Visitors
6. Access control
7. Alerts
8. Analytics
9. GenAI assistant
10. Settings

### UI rule

The sidebar should be generated from enabled modules:

```ts
const menu = allMenuItems.filter(item => enabledModules.includes(item.moduleKey));
```

But direct route access must still call the backend and fail with `403 Module disabled` if the feature is disabled.

---

## 13. Recommended Repository Structure

### Option A: Two repos

Use this if you want easy deployment:

- `visionpass-backend`
- `visionpass-frontend`

### Option B: Monorepo

Use this if you want one GitHub repo:

```txt
visionpass-ai/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   └── package.json
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── database-schema.md
│   └── demo-script.md
├── docker-compose.yml
├── README.md
└── .env.example
```

Recommended for you: **monorepo** during development, because it is easier to manage. You can still deploy frontend and backend separately.

---

## 14. Security Requirements

This project handles biometric data, so security must be treated seriously.

Required:

- JWT expiry and refresh flow.
- Strong password hashing using bcrypt/argon2.
- Role-based access control.
- Tenant isolation on every query.
- Feature-flag enforcement on backend routes.
- HTTPS only in production.
- CORS restricted to frontend domain.
- Audit logs for sensitive actions.
- Encrypt or strongly protect face embeddings.
- Never expose raw embeddings to frontend.
- Rate-limit login and recognition endpoints.
- Store secrets only in environment variables.

Important privacy point: avoid storing unnecessary face images. Store embeddings and minimal snapshots only when required for audit/demo.

---

## 15. GenAI Assistant Scope

Do not let GenAI query the entire database directly.

Use a controlled retrieval layer.

Allowed questions:

- “How many unknown visitors came today?”
- “Show attendance summary for this week.”
- “Who came late yesterday?”
- “Which camera generated the most alerts?”
- “Summarize access denied events this month.”

Implementation:

1. User asks natural-language question.
2. Backend identifies intent.
3. Backend runs safe SQL templates or controlled query functions.
4. Result is passed to LLM for explanation.
5. Response includes numbers and source table names.

Never allow free-form SQL generation without strict validation.

---

## 16. Build Roadmap

## Phase 0 — Product Foundation, 2-3 days

Deliverables:

- Final name and logo placeholder.
- Final module list.
- Database ERD.
- API route plan.
- UI wireframe.
- GitHub monorepo setup.

## Phase 1 — Backend Core, 5-7 days

Deliverables:

- FastAPI project.
- PostgreSQL connection.
- SQLAlchemy models.
- Alembic migrations.
- Auth and roles.
- Tenant middleware/dependencies.
- Feature flag system.
- Audit logs.

## Phase 2 — AI Engine MVP, 5-7 days

Deliverables:

- Phone/IP camera frame ingestion.
- Face detection.
- Face enrollment.
- Face recognition.
- Tenant-specific matching.
- Basic attendance event creation.
- Duplicate attendance prevention.

## Phase 3 — Frontend MVP, 6-8 days

Deliverables:

- Next.js app.
- Login page.
- Protected routes.
- Super-admin dashboard.
- Tenant create/edit.
- Module toggle UI.
- Client dashboard shell.
- Attendance screen.
- Employee management screen.

## Phase 4 — Pluggable Modules, 7-10 days

Deliverables:

- Visitor classification.
- Camera management.
- Access decision module.
- Alert module.
- Analytics module.
- Feature-flag-driven sidebar.
- Backend 403 enforcement for disabled modules.

## Phase 5 — GenAI + Anomaly, 5-7 days

Deliverables:

- Controlled GenAI query assistant.
- Query history.
- Rule-based anomaly detection.
- Alert creation from anomaly rules.
- Dashboard assistant page.

## Phase 6 — Deployment, 3-5 days

Deliverables:

- Dockerized backend.
- Hosted PostgreSQL.
- Backend deployed.
- Frontend deployed.
- Environment variables configured.
- Domain connected.
- HTTPS verified.
- Phone camera stream tested.

## Phase 7 — Demo Polish, 4-6 days

Deliverables:

- Three demo tenants.
- Seed employees and attendance logs.
- Demo camera feed.
- Admin toggle demonstration.
- Clean UI polish.
- Error handling.
- README and demo script.

---

## 17. Recommended MVP Scope

Build this first:

### Must-have

- Super-admin login.
- Tenant creation.
- Feature flags.
- Client login.
- Employee enrollment.
- Phone camera recognition.
- Attendance logging.
- Client dashboard.
- Admin module toggles.
- Tenant-safe database queries.

### Should-have

- Visitor classification.
- Alerts.
- Camera management.
- Analytics charts.
- Audit logs.

### Premium/demo features

- GenAI assistant.
- Anomaly detection.
- Access control decisions.
- Usage/billing analytics.

---

## 18. Demo Plan

Create three tenants:

### Client A — Basic Plan

Enabled modules:

- Attendance
- Employee Management

Demo story:

- Client A only sees attendance and employees.
- No visitor, alerts, or assistant menu appears.

### Client B — Security Plan

Enabled modules:

- Attendance
- Visitors
- Alerts
- Camera Management

Demo story:

- Unknown person creates visitor log and alert.

### Client C — Premium Plan

Enabled modules:

- Attendance
- Visitors
- Alerts
- Access Control
- Analytics
- GenAI Assistant
- Anomaly Detection

Demo story:

- Admin toggles GenAI assistant off and on.
- Client dashboard updates.
- User asks: “Summarize today’s unknown visitor alerts.”

This is the best interview moment because it proves centralized SaaS thinking.

---

## 19. Production Checklist

Before calling it complete:

- All routes require auth.
- All tenant routes filter by `tenant_id`.
- Disabled modules return 403.
- Client dashboard hides disabled modules.
- Super-admin can control modules.
- Passwords are hashed.
- Face embeddings are protected.
- `.env` is not committed.
- API has request validation.
- Backend has error responses.
- Frontend has loading/error states.
- Database migrations run cleanly.
- Deployment works from fresh environment.
- Demo tenants are seeded.
- README explains setup and demo.

---

## 20. Final Recommendation

Build the project as **VisionPass AI**.

Use a centralized monorepo with:

- FastAPI backend.
- PostgreSQL database.
- Next.js/React frontend.
- Tenant-based feature flags.
- Super-admin control panel.
- Dynamic client dashboard.
- CPU-friendly AI inference.
- Colab only for training/exporting liveness models.

The most important product principle is this:

> Never build separate apps for separate clients. Build one configurable platform where the admin controls what every tenant can access.
