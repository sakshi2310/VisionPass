# Vision Pass API overview

Vision Pass exposes a FastAPI application under `/api`. Interactive OpenAPI
documentation is available at `/docs`; the schema is `/openapi.json`.

## Authentication

Send access tokens as:

```http
Authorization: Bearer <access-token>
```

Authentication entry points:

| Audience | Endpoint |
|---|---|
| First platform owner | `POST /api/auth/bootstrap` |
| Super admin | `POST /api/admin/login` |
| Client admin | `POST /api/tenant/auth/login` |
| Tenant user | `POST /api/user/auth/login` |
| Current principal | `GET /api/auth/me` |
| Logout | `POST /api/auth/logout` |

Tenant IDs are taken from the authenticated principal. Client APIs do not accept
an arbitrary tenant scope except where a payload is explicitly checked against
the current tenant.

## Main resources

| Area | Base path | Highlights |
|---|---|---|
| Platform administration | `/api/admin` | Tenant CRUD, feature catalogue, audit logs, dashboard |
| Client administration | `/api/tenant-admin` | Members, tenant features, client dashboard |
| Attendance configuration | `/api/client-admin/attendance` | Settings, shifts, holidays, employees, face enrollment |
| Attendance operations | `/api/attendance` | Check-in, check-out, today, recognize, recognize-and-mark |
| Cameras | `/api/cameras` | CRUD, connection test, snapshot, recognition and attendance processing |
| Visitors | `/api/visitors` | Registration, check-in, check-out, visit history |
| Access control | `/api/access` | Access decisions and decision logs |
| Alerts | `/api/alerts` | List, acknowledge, resolve |
| Reports | `/api/reports` | Attendance, employees, visitors, cameras, recognition and access |
| Tenant user workspace | `/api/me` | Personal dashboard, attendance, profile and notifications |

## Reports and export

Report endpoints accept the filters relevant to the selected report:
`start_date`, `end_date`, `employee_id`, `department`, `status`, `camera_id`,
and `event_type`.

```http
GET /api/reports/attendance
GET /api/reports/employees
GET /api/reports/visitors
GET /api/reports/cameras
GET /api/reports/recognition
GET /api/reports/access
GET /api/reports/attendance/export.csv
GET /api/reports/access/export.csv
```

JSON reports return `{ "items": [...], "total": number }`. CSV endpoints return
an attachment. All report queries are tenant-scoped.

## Face recognition

Face enrollment accepts multipart image files. Images are validated for one
detectable face, resolution, size, brightness, sharpness, quality and
cross-employee duplication before an InsightFace embedding is stored.

Recognition never accepts a client-provided tenant ID. Matching considers only
active embeddings and employees from the authenticated tenant. No deterministic
or hash-based mock embedding path remains.

## Errors

The API uses standard HTTP status codes:

- `400` invalid operation
- `401` missing or invalid authentication
- `403` role, feature or tenant-scope denial
- `404` tenant-scoped resource not found
- `409` state conflict
- `422` request validation failure

Treat error response details as diagnostic text, not a stable programmatic code,
unless an endpoint schema documents a code field.
