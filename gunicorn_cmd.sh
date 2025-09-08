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
	# Helpful guidance for first-run / fresh installs
	echo "DATABASE_URL=${DATABASE_URL:-(using bundled sqlite by default)}"
	if [ -n "${DEFAULT_SUPERADMIN_EMAIL}" ] && [ -n "${DEFAULT_SUPERADMIN_PASSWORD}" ]; then
		echo "A default Super Admin will be auto-created on first-run: ${DEFAULT_SUPERADMIN_EMAIL} (password must be changed at first login)"
	elif [ "${AUTO_CREATE_SUPERADMIN:-0}" = "1" ]; then
		echo "AUTO_CREATE_SUPERADMIN=1 is set; a Super Admin will be auto-created with a temporary password printed to stdout on first-run."
	else
		echo "No auto Super Admin is configured. Use the web signup page to create the first Super Admin."
	fi
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
