from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid
import sys
import os

from .. import cleaner as cleaner_mod
from .. import report_generator as report_mod
from ..config import get_mongo_client, MONGODB_URI

# Add parent directory to path for utils import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from backend.utils.logger import get_logger

router = APIRouter()
logger = get_logger("cleandatapro.backend.process")

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports"

for d in (RAW_DIR, PROCESSED_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)


@router.post("/process")
async def process_upload(file: UploadFile = File(...)):
    """Accept a CSV upload, clean it and return JSON summary + paths to artifacts."""
    # validate filename exists and is a CSV
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # save uploaded file to data/raw with a unique name
    uid = uuid.uuid4().hex[:8]
    raw_name = f"{Path(file.filename).stem}_{uid}.csv"
    raw_path = RAW_DIR / raw_name

    try:
        with raw_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # clean the CSV file on disk using cleaner.clean_csv which reads/writes files
    processed_name = f"{Path(file.filename).stem}_{uid}_cleaned.csv"
    processed_path = PROCESSED_DIR / processed_name
    try:
        summary = cleaner_mod.clean_csv(str(raw_path), str(processed_path))
    except FileNotFoundError as e:
        logger.error("Failed to read uploaded CSV: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")
    except Exception as e:
        logger.exception("Failed during cleaning: %s", e)
        raise HTTPException(status_code=500, detail="Failed to clean CSV")

    # generate report (pdf) and json
    report_name = f"{Path(file.filename).stem}_{uid}_report.pdf"
    report_path = REPORTS_DIR / report_name
    json_name = f"{Path(file.filename).stem}_{uid}_summary.json"
    json_path = REPORTS_DIR / json_name

    try:
        report_mod.generate_pdf_report(
            summary, str(report_path), title=f"Summary: {file.filename}"
        )
        report_mod.save_json_summary(summary, str(json_path))
    except Exception as e:
        logger.exception("Failed to generate report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate report")

    # Try to persist run summary to MongoDB (best-effort: failures won't block response)
    if MONGODB_URI:
        try:
            client = get_mongo_client()
            if client:
                # prefer default database from URI, else use a sensible default
                try:
                    db = client.get_default_database()
                except Exception:
                    db = client["cleandatapro"]

                coll = db["clean_runs"]
                doc = {
                    "raw_file": str(raw_path.as_posix()),
                    "cleaned_file": str(processed_path.as_posix()),
                    "report_file": str(report_path.as_posix()),
                    "json_summary": str(json_path.as_posix()),
                    "summary": summary,
                    "uploaded_filename": file.filename,
                    "run_id": uid,
                }
                coll.insert_one(doc)
                logger.info("Persisted run summary to MongoDB (run_id=%s)", uid)
        except Exception as e:
            # best-effort: log but don't fail the request
            logger.warning("Failed to persist summary to MongoDB: %s", e)
        # Do NOT close the client here. `get_mongo_client()` returns a cached client
        # which should remain open for the lifetime of the application. Closing it
        # would prevent subsequent requests from reusing the connection.

    resp = {
        "raw_file": str(raw_path.as_posix()),
        "cleaned_file": str(processed_path.as_posix()),
        "report_file": str(report_path.as_posix()),
        "json_summary": str(json_path.as_posix()),
        "summary": summary,
    }

    return JSONResponse(status_code=200, content=resp)
