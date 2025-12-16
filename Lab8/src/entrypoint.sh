#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h db -p 5432 -U user > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up"

if [ "${SKIP_MIGRATIONS}" != "1" ]; then
  echo "Running migrations..."
  cd /app
  uv run alembic upgrade head
else
  echo "Skipping migrations (SKIP_MIGRATIONS=1)"
fi

echo "Starting application..."
cd /app/src
exec "$@"