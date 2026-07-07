# Vision Pass environment variables

Pydantic loads backend variables from the process environment or `backend/.env`.
Vite variables are embedded at frontend build time. Root `.env.example`
documents the production Compose values.

## Backend

| Variable | Default | Purpose |
|---|---|---|
| `APP_NAME` | `Vision Pass` | API display name |
| `ENVIRONMENT` | `development` | Runtime environment |
| `API_V1_PREFIX` | `/api` | API mount path |
| `DATABASE_URL` | local Vision Pass PostgreSQL | SQLAlchemy connection URL |
| `JWT_SECRET` | `change-me` | Token signing secret; required to change in production |
| `CORS_ORIGINS` | localhost origins | JSON list of allowed browser origins |
| `FRONTEND_URL` | unset | Public frontend URL |
| `SEED_DEMO_DATA` | `true` | Seed demo identities/data; set false in production |
| `FACE_MODEL_NAME` | `buffalo_l` | InsightFace model |
| `PRELOAD_FACE_MODEL` | `true` | Download and validate the model before the API starts |
| `FACE_DETECTION_CONFIDENCE` | `0.60` | Detection threshold |
| `FACE_RECOGNITION_THRESHOLD` | `0.45` | Match threshold |
| `FACE_ENROLLMENT_MIN_QUALITY` | `0.70` | Enrollment quality threshold |
| `FACE_DUPLICATE_THRESHOLD` | `0.40` | Cross-employee duplicate threshold |
| `ACCESS_CONFIDENCE_THRESHOLD` | `0.65` | Automatic access threshold |
| `ACCESS_UNKNOWN_FACE_ACTION` | `manual_review` | Unknown-person policy |
| `ACCESS_OUTSIDE_SHIFT_ACTION` | `manual_review` | Out-of-shift policy |
| `ACCESS_HOLIDAY_ACTION` | `manual_review` | Holiday policy |
| `ACCESS_SHIFT_GRACE_MINUTES` | `0` | Access shift grace |
| `ATTENDANCE_DUPLICATE_COOLDOWN_MINUTES` | `10` | Duplicate mark cooldown |
| `ATTENDANCE_LATE_GRACE_MINUTES` | `10` | Late threshold grace |
| `ATTENDANCE_AUTO_CHECKOUT_HOURS` | `12` | Automatic checkout horizon |
| `CAMERA_FRAME_INTERVAL_SECONDS` | `3` | UI/frame polling interval |
| `CAMERA_REQUEST_TIMEOUT_SECONDS` | `10` | Snapshot HTTP timeout |
| `STORAGE_BACKEND` | `local` | Current storage mode |
| `UPLOAD_DIR` | `uploads` | Local upload directory |
| `UPLOAD_MAX_IMAGE_MB` | `5` | Per-image upload limit |

## Compose/PostgreSQL

| Variable | Purpose |
|---|---|
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | Database user |
| `POSTGRES_PASSWORD` | Required URL-safe database password |
| `FRONTEND_PORT` | Published Nginx port, default `3000` |

## Frontend

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | API origin embedded at build time; leave empty for the production same-origin Nginx proxy |

Secrets must not be committed. Use a secret manager for public production
deployments and rotate any credentials used during a demo.
