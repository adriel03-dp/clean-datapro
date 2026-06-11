"""Frontend environment configuration."""

import os


def get_backend_base() -> str:
    explicit_url = os.environ.get("CLEAN_DATAPRO_BACKEND")
    if explicit_url:
        return explicit_url.rstrip("/")

    host = os.environ.get("CLEAN_DATAPRO_BACKEND_HOST")
    port = os.environ.get("CLEAN_DATAPRO_BACKEND_PORT")
    if host and port:
        return f"http://{host}:{port}"

    return "http://localhost:8000"


BACKEND_BASE = get_backend_base()
