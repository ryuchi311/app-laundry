"""Background DB keepalive to gently ping the database and reset connections when needed.

This module starts a single daemon thread that periodically runs a lightweight
query (SELECT 1). If the query fails (for example, MySQL closed the connection),
the engine pool is disposed to force new connections. The interval is intentionally
soft and configurable; default is 120 seconds.
"""
from __future__ import annotations

import threading
import time
import logging
import os
from typing import Optional

from sqlalchemy import text

logger = logging.getLogger("app.db_keepalive")

# Module-level flag to avoid starting multiple threads
_KEEPALIVE_THREAD: Optional[threading.Thread] = None


def _keepalive_loop(app, db, interval_seconds: int):
    logger.info("DB keepalive thread started (interval=%ds)", interval_seconds)
    while True:
        try:
            time.sleep(interval_seconds)
            with app.app_context():
                try:
                    # Lightweight check
                    db.session.execute(text("SELECT 1"))
                    db.session.commit()
                except Exception as e:
                    # If the DB connection is dead, dispose the pool so SQLAlchemy
                    # creates fresh connections on the next checkout.
                    logger.warning("DB keepalive query failed: %s; disposing engine", e)
                    try:
                        db.engine.dispose()
                    except Exception:
                        logger.exception("Failed to dispose DB engine")
        except Exception:
            # Protect loop from crashing; log and continue after a backoff
            logger.exception("Unexpected error in DB keepalive loop; sleeping briefly")
            time.sleep(min(60, interval_seconds))


def start_keepalive(app, db, *, interval_seconds: int = 120):
    """Start the DB keepalive thread if not already running.

    - interval_seconds: how often to ping the DB (default 120s). Keep this
      reasonably below your DB server's idle timeout. This routine is soft
      (sleeps between probes) and non-aggressive.
    """
    global _KEEPALIVE_THREAD
    if os.environ.get("ENABLE_DB_KEEPALIVE") == "0":
        logger.info("DB keepalive disabled via ENABLE_DB_KEEPALIVE=0")
        return

    if _KEEPALIVE_THREAD is not None and _KEEPALIVE_THREAD.is_alive():
        logger.debug("DB keepalive already running")
        return

    # Create and start a daemon thread
    t = threading.Thread(target=_keepalive_loop, args=(app, db, interval_seconds), daemon=True, name="db-keepalive")
    t.start()
    _KEEPALIVE_THREAD = t
    return t
