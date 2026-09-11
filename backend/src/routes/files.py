from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import urllib.parse

from ..storage import PROCESSED_DIR, RAW_DIR, REPORTS_DIR
from ..auth import get_current_user
from ..config import MONGODB_URI, get_mongo_client

router = APIRouter()

# simple whitelist directories we serve from
SERVE_DIRS = {
    "reports": REPORTS_DIR,
    "processed": PROCESSED_DIR,
    "raw": RAW_DIR,
}

ARTIFACT_FIELDS = {
    "reports": ("report_file", "json_summary"),
    "processed": ("cleaned_file",),
    "raw": ("raw_file",),
}


def _safe_resolve(dir_path: Path, filename: str) -> Path:
    # prevent path traversal
    decoded = urllib.parse.unquote(filename)
    candidate = (dir_path / decoded).resolve()
    base = dir_path.resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return candidate


@router.get("/download")
def download(
    kind: str = Query("processed"),
    filename: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Download a file.

    Query params:
      - kind: one of [processed, reports, raw]
      - filename: filename to download (URL-encoded safe)
    """
    if kind not in SERVE_DIRS:
        raise HTTPException(status_code=400, detail="Invalid kind")
    base = SERVE_DIRS[kind]
    target = _safe_resolve(base, filename)

    if not MONGODB_URI:
        raise HTTPException(status_code=503, detail="File ownership storage is unavailable")
    try:
        client = get_mongo_client()
        if not client:
            raise RuntimeError("MongoDB client unavailable")
        try:
            db = client.get_default_database()
        except Exception:
            db = client["cleandatapro"]
        ownership_filter = {
            "user_email": current_user["email"],
            "$or": [{field: str(target.as_posix())} for field in ARTIFACT_FIELDS[kind]],
        }
        if not db["clean_runs"].find_one(ownership_filter, {"_id": 1}):
            raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="File ownership storage is unavailable")
    return FileResponse(path=str(target), filename=target.name)
