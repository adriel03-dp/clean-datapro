from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from pathlib import Path
import uuid
import re
import pandas as pd

from .. import cleaner as cleaner_mod
from .. import report_generator as report_mod
from ..config import get_mongo_client, MONGODB_URI
from ..auth import get_current_user
from ..storage import RAW_DIR, PROCESSED_DIR, REPORTS_DIR

from utils.logger import get_logger

router = APIRouter()
logger = get_logger("cleandatapro.backend.process")
MAX_UPLOAD_BYTES = 100 * 1024 * 1024


def _safe_stem(filename: str) -> str:
    """Create a filesystem-safe dataset stem without trusting client input."""
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).stem).strip("._-")
    return (stem or "dataset")[:80]


async def _save_upload(file: UploadFile, destination: Path) -> int:
    """Stream an upload to disk and enforce the same limit as the web shell."""
    size = 0
    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="CSV file is larger than 100 MB")
                buffer.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except Exception as exc:
        destination.unlink(missing_ok=True)
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    return size


@router.post("/process")
async def process_upload(
    current_user: dict = Depends(get_current_user), file: UploadFile = File(...)
):
    """Accept a CSV upload, clean it and return JSON summary + paths to artifacts."""
    # validate filename exists and is a CSV
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save uploaded file to data/raw with an unguessable name.
    original_filename = Path(file.filename).name
    stem = _safe_stem(original_filename)
    uid = uuid.uuid4().hex
    raw_name = f"{stem}_{uid}.csv"
    raw_path = RAW_DIR / raw_name
    await _save_upload(file, raw_path)

    # clean the CSV file on disk using cleaner.clean_csv which reads/writes files
    processed_name = f"{stem}_{uid}_cleaned.csv"
    processed_path = PROCESSED_DIR / processed_name
    try:
        summary = await run_in_threadpool(
            cleaner_mod.clean_csv, str(raw_path), str(processed_path)
        )
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as e:
        logger.warning("Invalid uploaded CSV: %s", e)
        raw_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable CSV")
    except ValueError as e:
        logger.warning("Invalid CSV value: %s", e)
        raw_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded CSV contains invalid values")
    except Exception as e:
        logger.exception("Failed during cleaning: %s", e)
        raw_path.unlink(missing_ok=True)
        processed_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to clean CSV")

    # generate report (pdf) and json
    report_name = f"{stem}_{uid}_report.pdf"
    report_path = REPORTS_DIR / report_name
    json_name = f"{stem}_{uid}_summary.json"
    json_path = REPORTS_DIR / json_name

    try:
        await run_in_threadpool(
            report_mod.generate_pdf_report,
            summary, str(report_path), title=f"Summary: {file.filename}"
        )
        await run_in_threadpool(report_mod.save_json_summary, summary, str(json_path))
    except Exception as e:
        logger.exception("Failed to generate report: %s", e)
        for artifact in (raw_path, processed_path, report_path, json_path):
            artifact.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to generate report")

    user_email = current_user["email"]

    # MongoDB is also the ownership ledger for downloadable artifacts. If the
    # record cannot be written, do not return links that cannot be authorized.
    if not MONGODB_URI:
        raise HTTPException(status_code=503, detail="History storage is not configured")
    try:
        client = get_mongo_client()
        if not client:
            raise RuntimeError("MongoDB client unavailable")
        try:
            db = client.get_default_database()
        except Exception:
            db = client["cleandatapro"]

        doc = {
            "raw_file": str(raw_path.as_posix()),
            "cleaned_file": str(processed_path.as_posix()),
            "report_file": str(report_path.as_posix()),
            "json_summary": str(json_path.as_posix()),
            "summary": summary,
            "uploaded_filename": original_filename,
            "run_id": uid,
            "user_email": user_email,
        }
        db["clean_runs"].insert_one(doc)
        logger.info("Persisted run summary to MongoDB (run_id=%s)", uid)
    except Exception:
        logger.exception("Failed to persist processing run")
        for artifact in (raw_path, processed_path, report_path, json_path):
            artifact.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Unable to save processing history")

    resp = {
        "raw_file": str(raw_path.as_posix()),
        "cleaned_file": str(processed_path.as_posix()),
        "report_file": str(report_path.as_posix()),
        "json_summary": str(json_path.as_posix()),
        "summary": summary,
        "run_id": uid,
    }

    return JSONResponse(status_code=200, content=resp)
