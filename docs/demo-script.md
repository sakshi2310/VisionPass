# Vision Pass MVP demo setup and smoke checklist

## Start the demo

Docker is the recommended path:

```sh
cp .env.example .env
```

Set strong `POSTGRES_PASSWORD` and `JWT_SECRET` values, then set:

```dotenv
SEED_DEMO_DATA=true
```

Start and inspect:

```sh
docker compose up --build -d
docker compose ps
docker compose logs -f backend
```

Open `http://localhost:3000`.

## Seed an existing empty database

The standalone seed command applies all Alembic migrations, then creates the
complete demo dataset. It is idempotent, so it can be run again safely.

With the Docker stack running:

```sh
docker compose exec backend python scripts/seed_demo.py --force
```

For a backend running directly on the host:

```sh
cd backend
python scripts/seed_demo.py
```

The command reads `DATABASE_URL` from the environment or the active `.env`
file. Use `--no-operational-data` to create only accounts, the tenant, master
features, and feature assignments.

## Seeded credentials

These credentials exist only when `SEED_DEMO_DATA=true`.

| Role | Email | Password |
|---|---|---|
| Super admin | `admin@gmail.com` | `admin@123` |
| Client admin (database role `tenant_admin`) | `tenant.admin@visionpass.test` | `TenantAdmin@123` |
| Tenant user | `normal.user@visionpass.test` | `User@123456` |

The idempotent seed also creates the VisionPass Demo Tenant, three employees,
General Shift, Independence Day holiday, two manual cameras, current and prior
attendance records, a visitor visit, recognition/access history and one open
alert. It creates no biometric profile or fake embedding.

Never enable demo seeding on a public production deployment.

## MVP smoke test

Record pass/fail and evidence for every item.

- [ ] **Login:** Sign in as super admin, client admin and tenant user; confirm
  each reaches its own workspace and logout invalidates the session.
- [ ] **Tenant management:** As super admin, open the demo tenant, edit a safe
  field, inspect enabled features and confirm another tenant's resources are
  not exposed.
- [ ] **Employee creation:** As client admin, create an employee with a unique
  code/email, assign General Shift, edit it, deactivate it and reactivate it.
- [ ] **Face enrollment:** Upload the required real images for that employee;
  verify quality results, profile status and embedding count. Attempt a
  duplicate face on another employee and confirm rejection.
- [ ] **Recognition:** Submit a clear enrolled face and confirm MATCHED. Submit
  an unknown face and confirm it is not assigned to another employee.
- [ ] **Attendance marking:** Check in through recognition or manual action;
  verify the immutable event and today's daily row. Check out and verify total
  work time. Confirm cooldown blocks accidental duplicates.
- [ ] **Camera test:** Configure a camera URL reachable from the backend
  container, test it, capture a snapshot and run recognition. Manual seeded
  cameras are inventory examples and do not contain a live URL.
- [ ] **Reports:** Open each report, exercise date/employee/status/camera
  filters, export attendance/access CSV, and verify only demo-tenant data.
- [ ] **Alerts:** Open the seeded alert, acknowledge it, resolve it, and verify
  status timestamps.

## Resetting demo data

For a disposable demo environment only:

```sh
docker compose down -v
docker compose up --build -d
```

The `-v` option permanently removes database and application volumes. Do not use
it against an environment containing data you need.
