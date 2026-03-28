"""Langfuse logger wrapper for the API Layer.

Initializes a singleton Langfuse client. Falls back to DummyTrace
which prints to stdout when Langfuse is unavailable.
"""

import logging
import os

logger = logging.getLogger("api.langfuse")

_langfuse_client = None
_langfuse_init_attempted = False


class DummyTrace:
    """Fallback trace: logs to stdout so demo always shows activity."""

    def span(self, name: str = "", **kwargs):
        logger.info("[TRACE SPAN] %s | %s", name, kwargs)
        return self

    def update(self, **kwargs):
        logger.info("[TRACE UPDATE] %s", kwargs)
        return self

    def end(self, **kwargs):
        return self


def get_langfuse():
    """Return singleton Langfuse client, or None."""
    global _langfuse_client, _langfuse_init_attempted

    if _langfuse_init_attempted:
        return _langfuse_client

    _langfuse_init_attempted = True

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")

    if not all([public_key, secret_key, host]):
        logger.warning(
            "Langfuse env vars not set (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST). "
            "Tracing disabled — logging to stdout only."
        )
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        logger.info("Langfuse client initialized (host=%s)", host)
        return _langfuse_client
    except Exception as exc:
        logger.warning("Failed to initialize Langfuse: %s. Tracing disabled.", exc)
        return None


def create_trace(name: str, **kwargs):
    """Create a Langfuse trace, or DummyTrace if unavailable.

    Returns an object with .span() and .update() methods in both cases.
    """
    client = get_langfuse()
    if client is None:
        logger.info("[TRACE] %s | %s", name, kwargs)
        return DummyTrace()

    try:
        # client.trace() returns StatefulTraceClient with .span() and .update()
        return client.trace(name=name, **kwargs)
    except Exception as exc:
        logger.warning("Langfuse trace creation failed: %s", exc)
        return DummyTrace()


def flush():
    """Flush pending Langfuse events."""
    client = get_langfuse()
    if client is not None:
        try:
            client.flush()
        except Exception as exc:
            logger.warning("Langfuse flush failed: %s", exc)
