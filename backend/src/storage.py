"""Storage paths shared by backend routes."""

import os
import tempfile
from pathlib import Path


def _default_storage_root() -> Path:
    if os.environ.get("VERCEL"):
        return Path(tempfile.gettempdir()) / "cleandatapro"
    return Path(__file__).resolve().parents[2]


STORAGE_ROOT = Path(
    os.environ.get("CLEAN_DATAPRO_STORAGE_DIR", _default_storage_root())
).resolve()
DATA_DIR = STORAGE_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = STORAGE_ROOT / "reports"

for directory in (RAW_DIR, PROCESSED_DIR, REPORTS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
