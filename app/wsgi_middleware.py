"""Small WSGI middleware helpers for graceful handling of client disconnects."""
from typing import Iterable


class IgnoreBrokenPipeMiddleware:
    """Wrap a WSGI app and stop iterating the response if the client
    disconnects while the server is writing. This avoids noisy stack
    traces for BrokenPipeError/ConnectionResetError originating from
    clients closing the connection early.

    This middleware is intentionally tiny and dependency-free; it simply
    catches BrokenPipeError/ConnectionResetError during iteration and
    ensures the wrapped iterable is closed.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        result = self.app(environ, start_response)
        return self._iter_result(result)

    def _iter_result(self, result: Iterable[bytes]):
        try:
            for chunk in result:
                try:
                    yield chunk
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected; stop sending.
                    break
        finally:
            # Attempt to close the original result if it supports close().
            try:
                if hasattr(result, "close"):
                    result.close()
            except Exception:
                pass
