import os

from app import create_app, socketio

app = create_app()
import logging

# Reduce noisy BrokenPipeError tracebacks from eventlet's WSGI server when
# clients disconnect (for example when a user double-clicks or navigates away).
# Keep this conservative: only lower the eventlet-related loggers so other
# application logs are unaffected.
try:
    logging.getLogger("eventlet.wsgi").setLevel(logging.WARNING)
    logging.getLogger("eventlet").setLevel(logging.WARNING)
except Exception:
    pass


def _env_bool(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "on")


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("FLASK_RUN_PORT", 8080)))
    debug = _env_bool("DEBUG", _env_bool("FLASK_DEBUG", True))

    # Run the SocketIO-aware server. Respect HOST/PORT environment variables so
    # callers (or containers) can control where the app binds.
    socketio.run(app, host=host, port=port, debug=debug)
