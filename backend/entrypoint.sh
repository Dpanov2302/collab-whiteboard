#!/usr/bin/env sh
set -eu
: "${SECRET_KEY:?SECRET_KEY is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"
if [ "${ENV:-local}" = "production" ] && [ "${SECRET_KEY}" = "change-me" ]; then
  echo "Unsafe SECRET_KEY" >&2
  exit 1
fi
exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-2}
