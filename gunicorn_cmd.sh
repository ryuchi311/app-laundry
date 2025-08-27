#!/bin/sh
# Template runner for gunicorn so we can substitute $PORT at container runtime
: ${PORT:=8080}
GUNICORN_BIN="/workspaces/app-laundry/.venv/bin/gunicorn"
if [ -x "$GUNICORN_BIN" ]; then
	exec "$GUNICORN_BIN" main:app -b 0.0.0.0:${PORT} -k eventlet -w 1
else
	exec gunicorn main:app -b 0.0.0.0:${PORT} -k eventlet -w 1
fi
