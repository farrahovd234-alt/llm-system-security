"""Langfuse logger wrapper for the API Layer.
 
Initializes and provides a singleton Langfuse client.
Falls back to stdout logging if Langfuse is unavailable or not configured.
"""
 
import logging
import os
 
logger = logging.getLogger("api.langfuse")
 
_langfuse_client = None
_langfuse_init_attempted = False
 
 
def get_langfuse():
    """Return the singleton Langfuse client, or None if unavailable.
 
    Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST from env.
    If any key is missing or the SDK import fails, returns None and logs a
    warning once.
    """
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
    """Create a Langfuse trace. Returns the trace object or None."""
    client = get_langfuse()
    if client is None:
        logger.info("[TRACE] %s | %s", name, kwargs)
        return None
    return client.trace(name=name, **kwargs)
 
 
def flush():
    """Flush pending Langfuse events."""
    client = get_langfuse()
    if client is not None:
        client.flush()