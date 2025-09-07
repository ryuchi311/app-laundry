#!/usr/bin/env sh
set -e

# Entrypoint for Cloud Run: exec gunicorn with eventlet worker for SocketIO support.
# Respects $PORT and supports optional STARTUP_DEBUG=1 for diagnostics.

: ${PORT:=8080}

if [ -z "${PORT}" ]; then
	echo "[entrypoint] ERROR: PORT is not set"
	exit 1
fi

GUNICORN_BIN="$(command -v gunicorn || true)"

echo "[entrypoint] Starting gunicorn on 0.0.0.0:${PORT}"

if [ "${STARTUP_DEBUG:-0}" = "1" ]; then
	echo "==== STARTUP DEBUG ===="
	echo "User: $(id -u):$(id -g)"
	echo "Working dir: $(pwd)"
	echo "ENV PORT=${PORT}"
	echo "PATH=$PATH"
	echo "Which gunicorn: ${GUNICORN_BIN:-not found}"
	python - <<'PY'
import sys
print('python', sys.version)
try:
		import main
		print('Imported main OK')
except Exception as e:
		import traceback
		print('Error importing main:')
		traceback.print_exc()
PY
	echo "==== END STARTUP DEBUG ===="
fi

# Prefer whatever gunicorn is installed in PATH; this will typically be the one
# installed in the container environment. Exec replaces the shell so signals
# are forwarded to gunicorn as PID 1 (required for Cloud Run graceful shutdown).
if [ -n "${GUNICORN_BIN}" ]; then
	exec ${GUNICORN_BIN} main:app -b 0.0.0.0:${PORT} -k eventlet -w 1 --log-level info
else
	echo "[entrypoint] gunicorn not found in PATH"
	exit 2
fi
