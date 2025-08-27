import os

from app import create_app, socketio

app = create_app()


def _env_bool(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "on")


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("FLASK_RUN_PORT", 5000)))
    debug = _env_bool("DEBUG", _env_bool("FLASK_DEBUG", True))

    # Run the SocketIO-aware server. Respect HOST/PORT environment variables so
    # callers (or containers) can control where the app binds.
    socketio.run(app, host=host, port=port, debug=debug)
