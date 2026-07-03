#!/bin/sh
set -eu

echo "Applying database migrations..."
attempt=1
until alembic upgrade head; do
  if [ "$attempt" -ge 10 ]; then
    echo "Database migrations failed after $attempt attempts." >&2
    exit 1
  fi
  echo "Migration attempt $attempt failed; retrying in 3 seconds..." >&2
  attempt=$((attempt + 1))
  sleep 3
done

echo "Database migrations are current."
exec "$@"
