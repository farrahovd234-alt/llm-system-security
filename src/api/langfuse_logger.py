"""Langfuse logger wrapper compatible with current SDK."""

import logging
import os
from typing import Any, Optional

logger = logging.getLogger("api.langfuse")

_langfuse_client = None
_langfuse_init_attempted = False

class DummyTrace:
    """Fallback trace object that keeps app code working when tracing is unavailable."""

    def span(self, name: str, **kwargs):
        logger.info("[SPAN disabled] %s | %s", name, kwargs)
        return None

    def update(self, **kwargs):
        logger.info("[TRACE UPDATE disabled] %s", kwargs)
        return None

class TraceAdapter:
    """Compatibility adapter for code expecting old trace.span()/trace.update() API."""

    def __init__(self, client, name: str, **kwargs):
        self.client = client
        self.name = name
        self.trace_id = client.create_trace_id()

        # try to initialize trace-level metadata
        try:
            payload = {}
            for key in ("input", "output", "user_id", "session_id", "metadata", "tags"):
                if key in kwargs:
                    payload[key] = kwargs[key]

            if payload:
                self.client.update_current_trace(trace_id=self.trace_id, name=name, **payload)
            else:
                self.client.update_current_trace(trace_id=self.trace_id, name=name)
        except Exception as exc:
            logger.warning("Failed to initialize Langfuse trace: %s", exc)

    def span(self, name: str, **kwargs):
        try:
            span_kwargs = {
                "trace_id": self.trace_id,
                "name": name,
            }

            for key in ("input", "output", "metadata", "user_id", "session_id", "level", "status_message"):
                if key in kwargs:
                    span_kwargs[key] = kwargs[key]

            return self.client.start_span(**span_kwargs)
        except Exception as exc:
            logger.warning("Failed to create Langfuse span '%s': %s", name, exc)
            return None

    def update(self, **kwargs):
        try:
            self.client.update_current_trace(trace_id=self.trace_id, **kwargs)
        except Exception as exc:
            logger.warning("Failed to update Langfuse trace: %s", exc)

def get_langfuse():
    global _langfuse_client, _langfuse_init_attempted

    if _langfuse_init_attempted:
        return _langfuse_client

    _langfuse_init_attempted = True

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")

    if not all([public_key, secret_key, host]):
        logger.warning("Langfuse env vars not set. Tracing disabled.")
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
        logger.warning("Failed to initialize Langfuse: %s", exc)
        return None

def create_trace(name: str, **kwargs):
    client = get_langfuse()
    if client is None:
        logger.info("[TRACE disabled] %s | %s", name, kwargs)
        return DummyTrace()

    try:
        return TraceAdapter(client, name=name, **kwargs)
    except Exception as exc:
        logger.warning("Langfuse trace adapter init failed: %s", exc)
        return DummyTrace()

def flush():
    client = get_langfuse()
    if client is not None:
        try:
            client.flush()
        except Exception as exc:
            logger.warning("Langfuse flush failed: %s", exc)