#!/usr/bin/env bash

if [ -f /app/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=/app/gunicorn_conf.py
elif [ -f /app/project/gunicorn_conf.py ]; then
    DEFAULT_GUNICORN_CONF=/app/project/gunicorn_conf.py
else
    DEFAULT_GUNICORN_CONF=/gunicorn_conf.py
fi

export GUNICORN_CONF=${GUNICORN_CONF:-$DEFAULT_GUNICORN_CONF}
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}
export LOGGER_CLASS=${LOGGER_CLASS:-"core.logging.GunicornLogger"}
export PORT=8000
export APP_NAME=fastapi-simple-auth

exec gunicorn app.main:app \
  --bind 0.0.0.0:$PORT \
  -k "$WORKER_CLASS" \
  -c "$GUNICORN_CONF" \
  --logger-class "$LOGGER_CLASS" \
  --forwarded-allow-ips "*" \
  --name $APP_NAME
