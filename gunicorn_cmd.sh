#!/bin/sh
# Template runner for gunicorn so we can substitute $PORT at container runtime
: ${PORT:=8080}
GUNICORN_BIN="/workspaces/app-laundry/.venv/bin/gunicorn"

# Optional startup diagnostics to help Cloud Run debugging
if [ "${STARTUP_DEBUG:-0}" = "1" ]; then
	echo "==== STARTUP DEBUG ===="
	echo "User: $(id -u):$(id -g)"
	echo "Working dir: $(pwd)"
	echo "ENV PORT=${PORT}"
	echo "PATH=$PATH"
	echo "Which gunicorn: $(which gunicorn 2>/dev/null || echo 'not in PATH')"
	if [ -x "$GUNICORN_BIN" ]; then
		echo "VENV gunicorn found at $GUNICORN_BIN"
	fi
	echo "Installed packages (pip list -l):"
	(python -m pip show gunicorn 2>/dev/null || true) && python -m pip --disable-pip-version-check list
	echo "Attempt to import main module:"
	python - <<'PY'
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

# Exec gunicorn (prefer venv binary if present). Use debug log level for more verbose logs.
if [ -x "$GUNICORN_BIN" ]; then
	exec "$GUNICORN_BIN" main:app -b 0.0.0.0:${PORT} -k eventlet -w 1 --log-level debug
else
	exec gunicorn main:app -b 0.0.0.0:${PORT} -k eventlet -w 1 --log-level debug
fi
