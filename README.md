# VisionPass AI

Monorepo scaffold for the centralized AI gate platform.
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
