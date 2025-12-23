from fastapi import APIRouter, Request, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Any

from ..config import get_mongo_client, MONGODB_URI
from ..auth import verify_token

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
REPORTS_DIR = BASE_DIR / "reports"


def _read_json_summaries() -> List[Dict[str, Any]]:
    out = []
    for p in sorted(REPORTS_DIR.glob("*_summary.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                metadata = {
                    "json_file": str(p.as_posix()),
                    "summary": data,
                }
                out.append(metadata)
        except Exception:
            continue
    return out


@router.get("/runs")
def list_runs(request: Request, limit: int = 50):
    """Return recent processing runs.

    If MongoDB is configured, read from the `clean_runs` collection. Otherwise
    return JSON summaries found in `reports/`.
    """
    if MONGODB_URI:
        # Require auth for per-user history when MongoDB is configured
        auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")

        token = auth_header.split(" ", 1)[1].strip()
        email = verify_token(token)
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            client = get_mongo_client()
            if client:
                try:
                    db = client.get_default_database()
                except Exception:
                    db = client["cleandatapro"]
                docs = list(
                    db["clean_runs"]
                    .find({"user_email": email})
                    .sort("_id", -1)
                    .limit(limit)
                )
                # convert ObjectId and other non-JSON types to strings
                for d in docs:
                    d["_id"] = str(d.get("_id"))
                return {"source": "mongodb", "runs": docs}
        except Exception:
            # fall back to filesystem
            pass
        # Do NOT close the client here. `get_mongo_client()` returns a cached client
        # intended to be reused for the lifetime of the app.

    # fallback
    files = _read_json_summaries()
    return {"source": "filesystem", "runs": files[:limit]}
