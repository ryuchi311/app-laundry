"""Lightweight request and SQL monitoring helpers.

This module provides two quick helpers:
- request timing: logs requests that exceed a configurable threshold
- SQL timing: logs SQL statements that take longer than a threshold

The hooks are safe to register during app creation and are disabled when
running under pytest unless explicitly enabled via env var.
"""
from __future__ import annotations

import logging
import time
import os
from typing import Any

from flask import g, request
from sqlalchemy import event

logger = logging.getLogger("app.monitoring")


def init_monitoring(app, db, *, req_threshold_ms: int = 500, query_threshold_ms: int = 200):
    """Register request and SQL timing hooks.

    - req_threshold_ms: requests longer than this (ms) are logged at WARNING.
    - query_threshold_ms: SQL statements longer than this (ms) are logged at WARNING.
    """
    # Only enable in non-test runs unless the env var ENABLE_REQUEST_MONITORING=1
    running_under_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST")) or any(
        "pytest" in str(a) for a in getattr(app, "cli_args", [])
    )
    if running_under_pytest and os.environ.get("ENABLE_REQUEST_MONITORING") != "1":
        app.config["REQUEST_MONITORING_ENABLED"] = False
        return

    app.config["REQUEST_MONITORING_ENABLED"] = True
    app.config.setdefault("REQUEST_MONITORING_THRESHOLD_MS", req_threshold_ms)
    app.config.setdefault("SQL_MONITORING_THRESHOLD_MS", query_threshold_ms)

    @app.before_request
    def _start_timer():
        g._req_start_time = time.perf_counter()

    @app.after_request
    def _log_slow_request(response):
        try:
            start = getattr(g, "_req_start_time", None)
            if start is None:
                return response
            elapsed_ms = (time.perf_counter() - start) * 1000
            threshold = app.config.get("REQUEST_MONITORING_THRESHOLD_MS", req_threshold_ms)
            if elapsed_ms >= threshold:
                logger.warning(
                    "Slow request: %s %s took %.1fms (threshold=%dms)",
                    request.method,
                    request.path,
                    elapsed_ms,
                    threshold,
                )
        except Exception:
            # Do not let monitoring break requests
            logger.exception("Error measuring request time")
        return response

    # SQL timing: attach to DB API cursor events. Use db.engine when app context is ready.
    try:
        engine = db.engine

        @event.listens_for(engine, "before_cursor_execute")
        def _sql_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.perf_counter()

        @event.listens_for(engine, "after_cursor_execute")
        def _sql_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            try:
                start = getattr(context, "_query_start_time", None)
                if start is None:
                    return
                elapsed_ms = (time.perf_counter() - start) * 1000
                qthreshold = app.config.get("SQL_MONITORING_THRESHOLD_MS", query_threshold_ms)
                if elapsed_ms >= qthreshold:
                    # Shorten long statements in logs
                    short_stmt = (statement or "").strip().replace("\n", " ")[:1000]
                    logger.warning(
                        "Slow SQL (%.1fms >= %dms): %s; params=%s",
                        elapsed_ms,
                        qthreshold,
                        short_stmt,
                        parameters,
                    )
            except Exception:
                logger.exception("Error measuring SQL time")
    except Exception:
        logger.exception("Could not attach SQL monitoring listeners")
