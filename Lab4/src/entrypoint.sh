#!/bin/bash
set -e
cd /app/src

echo "Waiting for PostgreSQL to be ready..."

until pg_isready -h db -p 5432 -U user > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - creating tables if they don't exist..."
python create_tables.py

echo "Starting application..."
exec "$@"
