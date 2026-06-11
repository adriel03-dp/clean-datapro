from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import urllib.parse

from ..storage import PROCESSED_DIR, RAW_DIR, REPORTS_DIR

router = APIRouter()

# simple whitelist directories we serve from
SERVE_DIRS = {
    "reports": REPORTS_DIR,
    "processed": PROCESSED_DIR,
    "raw": RAW_DIR,
}


def _safe_resolve(dir_path: Path, filename: str) -> Path:
    # prevent path traversal
    decoded = urllib.parse.unquote(filename)
    candidate = (dir_path / decoded).resolve()
    if not str(candidate).startswith(str(dir_path.resolve())):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


@router.get("/download")
def download(kind: str = Query("processed"), filename: str = Query(...)):
    """Download a file.

    Query params:
      - kind: one of [processed, reports, raw]
      - filename: filename to download (URL-encoded safe)
    """
    if kind not in SERVE_DIRS:
        raise HTTPException(status_code=400, detail="Invalid kind")
    base = SERVE_DIRS[kind]
    target = _safe_resolve(base, filename)
    return FileResponse(path=str(target), filename=target.name)
