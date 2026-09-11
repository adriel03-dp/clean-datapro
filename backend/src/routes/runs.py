from fastapi import APIRouter, Depends, HTTPException, Query

from ..config import get_mongo_client, MONGODB_URI
from ..auth import get_current_user

router = APIRouter()


@router.get("/runs")
def list_runs(current_user: dict = Depends(get_current_user), limit: int = Query(50, ge=1, le=100)):
    """Return recent processing runs.

    If MongoDB is configured, read from the `clean_runs` collection. Otherwise
    return JSON summaries found in `reports/`.
    """
    if not MONGODB_URI:
        raise HTTPException(status_code=503, detail="History storage is not configured")

    try:
        client = get_mongo_client()
        if client is None:
            raise RuntimeError("MongoDB client unavailable")
        try:
            db = client.get_default_database()
        except Exception:
            db = client["cleandatapro"]
        docs = list(
            db["clean_runs"]
            .find({"user_email": current_user["email"]})
            .sort("_id", -1)
            .limit(limit)
        )
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return {"source": "mongodb", "runs": docs}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="History storage is temporarily unavailable")
