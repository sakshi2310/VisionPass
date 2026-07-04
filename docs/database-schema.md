# Vision Pass database overview

Vision Pass uses PostgreSQL 16 with `pgcrypto` and `vector`. Alembic migrations
are the source of truth; run `alembic upgrade head` rather than creating tables
from ORM metadata.

## Core tables

| Domain | Tables |
|---|---|
| Platform | `super_admins`, `tenants`, `features` |
| Membership | `tenant_members`, `tenant_features`, `member_features`, `auth_sessions` |
| Audit | `audit_logs` |
| Attendance configuration | `attendance_settings`, `attendance_working_days`, `attendance_shifts`, `attendance_holidays`, `attendance_face_settings` |
| Employees and biometrics | `attendance_employees`, `employee_face_profiles`, `employee_face_images`, `employee_face_embeddings` |
| Attendance activity | `attendance_events`, `daily_attendance_records` |
| Cameras and recognition | `cameras`, `camera_events` |
| Visitors | `visitors`, `visitor_visits` |
| Access and alerts | `access_logs`, `alerts` |

## Isolation and integrity

- Tenant-owned tables contain a non-null `tenant_id` foreign key.
- Employee codes and emails are unique within a tenant.
- Daily attendance is unique by tenant, employee and date.
- Face profiles are unique by tenant and employee.
- Tenant/member feature grants have scoped unique constraints.
- Operational status and event-type check constraints reject invalid states.
- Tenant and time indexes support dashboard and report queries.

## Face data

Validated source images currently use data URLs in
`employee_face_images.image_url`. Embeddings use pgvector with 512 dimensions
and an HNSW cosine-distance index. `embedding_model`, version and quality
metadata are retained. The old mock embedding migration deactivates and removes
historical `mock-face-embedder` rows; it does not create mock data.

## Migration workflow

```sh
cd backend
alembic current
alembic upgrade head
alembic history
```

Production containers run the upgrade automatically. Before releasing a new
migration, verify both an upgrade of an existing database and an upgrade from a
new empty PostgreSQL database.

## Backup

Use `pg_dump`/`pg_restore` for logical backups. A raw copy of a mounted live
PostgreSQL volume is not a safe backup. Back up the local upload volume
separately if file-backed features are introduced.
