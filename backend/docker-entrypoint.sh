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

if [ "${PRELOAD_FACE_MODEL:-true}" = "true" ]; then
  echo "Preparing InsightFace model..."
  attempt=1
  until python -m scripts.ensure_face_model; do
    if [ "$attempt" -ge 3 ]; then
      echo "InsightFace model preparation failed after $attempt attempts." >&2
      exit 1
    fi
    echo "Model preparation attempt $attempt failed; retrying in 10 seconds..." >&2
    attempt=$((attempt + 1))
    sleep 10
  done
fi
exec "$@"
