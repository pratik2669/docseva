#!/usr/bin/env sh
# DocSeva production entrypoint
# Runs migrations, seeds data, collects static files, then hands off to CMD.
set -e

echo "[entrypoint] Running database migrations…"
python manage.py migrate --noinput

echo "[entrypoint] Seeding default subscription plans…"
python manage.py create_default_plans

echo "[entrypoint] Collecting static files…"
python manage.py collectstatic --noinput --clear

echo "[entrypoint] Starting server…"
exec "$@"
