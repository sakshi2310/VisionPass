# Vision Pass architecture overview

## Runtime

```text
Browser
  |
  v
Nginx frontend (React/Vite SPA)
  |  /api reverse proxy
  v
FastAPI backend
  |
  +-- SQLAlchemy/Alembic --> PostgreSQL 16 + pgvector
  +-- InsightFace/ONNX Runtime --> face detection and embeddings
  +-- HTTP camera client --> configured snapshot cameras
```

The production Compose topology contains `frontend`, `backend`, and
`postgres`. Redis and MinIO are absent because no active application path uses
them.

## Repository

| Path | Responsibility |
|---|---|
| `frontend/src` | Active Vite React application |
| `backend/app/api/v1/endpoints` | HTTP routes and authorization boundaries |
| `backend/app/services` | Tenant-scoped business operations |
| `backend/app/models` | SQLAlchemy persistence models |
| `backend/app/schemas` | Pydantic request/response contracts |
| `backend/alembic` | Ordered database migrations |
| `backend/tests` | Integration and service tests |
| `docs` | Operator and MVP documentation |

## Tenant isolation

Tenant members carry a database-backed `tenant_id`. Dependencies load the
authenticated member and reject inactive accounts or tenants. Services receive
that tenant ID from the authenticated principal, and resource queries constrain
the primary table and joined tenant-owned tables. Super-admin endpoints are
separate from tenant operational endpoints.

## Recognition flow

1. An authenticated caller uploads an image or requests a camera snapshot.
2. The backend decodes and validates the frame.
3. InsightFace produces a normalized 512-dimensional embedding.
4. pgvector cosine distance finds active candidates in the same tenant.
5. The tenant face threshold determines matched, unknown, or low-confidence.
6. Recognition, camera, attendance, access and audit records are persisted as
   applicable.

The MVP seed intentionally creates no face embeddings. A real face must be
enrolled during the demo.

## Attendance model

`attendance_events` is the immutable check-in/check-out stream.
`daily_attendance_records` is the per-employee daily projection used by live
attendance and reports. Settings, shifts, working days and holidays are
tenant-owned configuration.

## Deployment behavior

The backend container waits for PostgreSQL, runs `alembic upgrade head`, then
starts Uvicorn. Nginx serves immutable Vite assets, falls back to `index.html`
for client routes, and proxies `/api`. PostgreSQL, uploads and the InsightFace
cache use named volumes. See the root README for commands and production
limitations.
