# Vision Pass

Vision Pass is a multi-tenant attendance, face-recognition, visitor, camera and
access-control platform. The MVP uses a React/Vite frontend, FastAPI backend,
PostgreSQL/pgvector persistence and InsightFace inference.

Implemented MVP areas include platform/tenant administration, role-based
workspaces, employees and face enrollment, attendance, cameras, visitors,
access decisions, alerts and tenant-isolated reports with CSV export.

## Documentation

- [API overview](docs/api.md)
- [Architecture overview](docs/architecture.md)
- [Database overview](docs/database-schema.md)
- [Role permissions](docs/role-permissions.md)
- [Environment variables](docs/environment-variables.md)
- [Demo setup and smoke checklist](docs/demo-script.md)

## Quick start for the MVP demo

```sh
cp .env.example .env
```

Set strong `POSTGRES_PASSWORD` and `JWT_SECRET` values and change
`SEED_DEMO_DATA` to `true`, then run:

```sh
docker compose up --build -d
docker compose ps
```

Open `http://localhost:3000`. Seeded demo credentials and the complete
presentation checklist are in [docs/demo-script.md](docs/demo-script.md).

Backend environment variables and their safe development defaults are documented
in `backend/.env.example`. Copy that file to `backend/.env` when running the API
from the backend directory; every listed setting is optional at startup.

## Production Docker deployment

The production Compose stack runs three services:

- `postgres`: PostgreSQL 16 with pgvector
- `backend`: FastAPI/InsightFace API; applies Alembic migrations before starting
- `frontend`: an Nginx-served Vite build that proxies `/api` to the backend

Redis and MinIO are intentionally not included because the application does not
currently use either service. PostgreSQL data, the local upload directory, and
the InsightFace model cache use named Docker volumes.

### Prerequisites

- Docker Engine with Docker Compose v2
- At least 4 GB RAM available to Docker (more is recommended for face recognition)
- Internet access for the initial image build and the first InsightFace model download

### Configure and start

From the repository root:

```sh
cp .env.example .env
```

Replace `POSTGRES_PASSWORD` and `JWT_SECRET` in `.env` with strong, URL-safe
random values (letters, numbers, `_`, `-`). Set `FRONTEND_URL` and
`CORS_ORIGINS` to the real HTTPS origin when
deploying behind a public reverse proxy. Keep `VITE_API_BASE_URL` empty to use
the Nginx same-origin API proxy.

Build and start the complete stack:

```sh
docker compose up --build -d
docker compose ps
```

The UI is available at `http://localhost:3000` by default. With
`SEED_DEMO_DATA=false`, open `/signup` on the first deployment to create the
platform owner. Do not enable demo seeding in a public deployment because it
creates documented development credentials.

### Operations

```sh
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

`docker compose down` preserves named volumes. To deploy a new version, pull or
copy the updated source and run `docker compose up --build -d` again. The
backend entrypoint runs `alembic upgrade head` before every API start.

Useful checks:

```sh
docker compose ps
curl http://localhost:3000/health
curl http://localhost:3000/api/reports/attendance
```

The second API check is expected to return `401` without an access token; that
still confirms routing through Nginx to FastAPI.

### Persistent data and backups

- `vision-pass_postgres_data`: application data, embeddings, and current face-image data URLs
- `vision-pass_uploads_data`: local file storage mounted at `/app/uploads`
- `vision-pass_insightface_cache`: downloaded InsightFace model files

Back up the PostgreSQL volume with `pg_dump`; copying a live database volume is
not a safe logical backup. Back up the upload volume separately if local file
features are enabled.

### Known deployment limitations

- TLS termination is not included. Put the frontend behind a production HTTPS
  reverse proxy or load balancer.
- Face enrollment currently stores accepted face images as data URLs in
  PostgreSQL; MinIO/S3 object storage is not implemented. The upload volume is
  available for visitor and future local-file storage.
- InsightFace downloads the configured model on first use, so that first
  recognition/enrollment request is slower and requires outbound network access.
- Alembic runs in each backend container at startup. Use a one-off migration job
  before scaling the backend to multiple replicas.
- Camera URLs must be reachable from the backend container's Docker network;
  host-only `localhost` camera URLs will point at the container itself.
- Docker secrets and automated PostgreSQL backups are not configured by this
  repository.

## Local face enrollment

Face enrollment uses InsightFace `buffalo_l` with ONNX Runtime on the server.
The model is loaded lazily on the first enrollment request; InsightFace downloads
the model into the current user's `.insightface` cache if it is not already
installed. Uploaded files are decoded and checked for exactly one face,
detection confidence, resolution, sharpness, brightness, face size, and overall
quality before a real 512-dimensional embedding is saved.
Embeddings are L2-normalized before pgvector storage. Enrollment also compares
each new embedding with active embeddings for other employees in the same
tenant. A cosine similarity at or above `FACE_DUPLICATE_THRESHOLD` is rejected;
the same face may be enrolled independently in another tenant.

Authenticated tenant users can recognize an enrolled employee with
`POST /api/attendance/recognize`. The endpoint accepts either multipart form
data (`image`, optional `camera_id`, optional `mode`) or JSON containing
`image`/`base64_frame`. Matching uses cosine similarity against active
embeddings and employees in the authenticated tenant only, with
`FACE_RECOGNITION_THRESHOLD` as the minimum match confidence. Every attempt is
written to the audit log.

Attendance tracking uses `attendance_events` as the immutable event stream and
`daily_attendance_records` as the tenant-local daily summary. Manual/web clients
can call `/api/attendance/check-in` and `/api/attendance/check-out`; camera flows
use `/api/attendance/recognize-and-mark`. Cooldown and late-grace decisions come
from `ATTENDANCE_DUPLICATE_COOLDOWN_MINUTES` and
`ATTENDANCE_LATE_GRACE_MINUTES`. Client admins can monitor the flow from
`/client-admin/attendance/live`.

Tenant and Client Admins manage camera sources from `/client-admin/cameras`.
IP Webcam cameras use their HTTP snapshot URL; Vision Pass fetches snapshots
with `CAMERA_REQUEST_TIMEOUT_SECONDS`, validates the response by decoding the
image, and updates camera health. Camera passwords are encrypted at rest and
are never returned by the API.

Live camera processing is available at `/client-admin/cameras/live` and through
the camera `process-frame`, `recognize-frame`, and
`recognize-and-mark-attendance` endpoints. Every attempt writes a tenant-scoped
`camera_events` row. The UI observes `CAMERA_FRAME_INTERVAL_SECONDS`; snapshot
requests use `CAMERA_REQUEST_TIMEOUT_SECONDS`, and matching continues to use
`FACE_RECOGNITION_THRESHOLD`.

```powershell
cd backend
.\venv\python.exe -m pip install -r requirements.txt
.\venv\python.exe -m pytest tests\test_face_ai_service.py tests\test_face_duplicate.py tests\test_config.py -q
.\venv\python.exe -m pytest tests\test_recognition_service.py tests\test_recognition_audit.py -q
.\venv\python.exe -m pytest tests\test_attendance_marking.py -q
.\venv\python.exe -m pytest tests\test_camera_snapshot.py tests\test_cameras.py -q
.\venv\python.exe -m pytest tests\test_camera_frame_service.py -q
```

On Windows, the PyPI InsightFace package builds a small native extension and
requires Microsoft C++ Build Tools 14 or newer. Linux environments need a C/C++
compiler toolchain. The API itself still starts without loading the model;
model initialization happens only when face enrollment is requested.

 .\venv\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

## Repository layout

```txt
backend/
  app/
    api/v1/endpoints/
    core/
    db/
    models/
    schemas/
    services/
    utils/
  tests/
  alembic/
frontend/
  app/
  components/
  lib/
  hooks/
  public/
docs/
```

## Build order

1. Foundation and repo structure
2. Backend core
3. Database models and migrations
4. Auth and tenant isolation
5. Feature flags and audit logs
6. Frontend shell
7. Module-by-module product screens
