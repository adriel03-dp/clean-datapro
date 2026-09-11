"""CSV processing routes with a pollable background-job workflow."""

from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
import re
import time
import uuid

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from .. import cleaner as cleaner_mod
from .. import report_generator as report_mod
from ..auth import get_current_user
from ..config import MONGODB_URI, get_mongo_client
from ..storage import PROCESSED_DIR, RAW_DIR, REPORTS_DIR
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("cleandatapro.backend.process")

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
JOB_TTL_SECONDS = 60 * 60
_JOBS: dict[str, dict[str, Any]] = {}
_JOBS_LOCK = Lock()


class ProcessingFailure(Exception):
    """A processing failure with a safe, user-facing message."""

    def __init__(self, code: str, public_message: str):
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_stem(filename: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).stem).strip("._-")
    return (stem or "dataset")[:80]


def _cleanup_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    with _JOBS_LOCK:
        expired = [job_id for job_id, job in _JOBS.items() if job["created_epoch"] < cutoff]
        for job_id in expired:
            _JOBS.pop(job_id, None)


def _update_job(job_id: str, **changes: Any) -> None:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is not None:
            job.update(changes)
            job["updated_at"] = _utc_now()


def _job_log(
    job_id: str,
    message: str,
    *,
    progress: int | None = None,
    stage: str | None = None,
    level: str = "info",
) -> None:
    entry = {"time": _utc_now(), "message": message, "level": level}
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return
        job["logs"].append(entry)
        job["logs"] = job["logs"][-40:]
        if progress is not None:
            job["progress"] = max(0, min(100, progress))
        if stage is not None:
            job["stage"] = stage
        job["updated_at"] = entry["time"]


def _remove_artifacts(paths: tuple[Path, ...]) -> None:
    for path in paths:
        path.unlink(missing_ok=True)


async def _save_upload(file: UploadFile, destination: Path) -> int:
    size = 0
    try:
        with destination.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="CSV file is larger than 100 MB")
                buffer.write(chunk)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        logger.exception("Failed to persist uploaded CSV")
        raise HTTPException(status_code=500, detail="Upload could not be accepted")
    return size


def _persist_run(
    *,
    original_filename: str,
    run_id: str,
    user_email: str,
    raw_path: Path,
    processed_path: Path,
    report_path: Path,
    json_path: Path,
    summary: dict[str, Any],
) -> None:
    safe_message = "The cleaning run could not be saved to your workspace. Please try again."
    if not MONGODB_URI:
        raise ProcessingFailure("history_unavailable", safe_message)

    client = get_mongo_client()
    if client is None:
        raise ProcessingFailure("history_unavailable", safe_message)

    try:
        try:
            db = client.get_default_database()
        except Exception:
            db = client["cleandatapro"]
        db["clean_runs"].insert_one(
            {
                "raw_file": str(raw_path.as_posix()),
                "cleaned_file": str(processed_path.as_posix()),
                "report_file": str(report_path.as_posix()),
                "json_summary": str(json_path.as_posix()),
                "summary": summary,
                "uploaded_filename": original_filename,
                "run_id": run_id,
                "user_email": user_email,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception as exc:
        logger.exception("Failed to persist processing run %s", run_id)
        raise ProcessingFailure("history_unavailable", safe_message) from exc


def _process_saved_upload(
    job_id: str,
    original_filename: str,
    run_id: str,
    user_email: str,
    raw_path: Path,
) -> dict[str, Any]:
    stem = _safe_stem(original_filename)
    processed_path = PROCESSED_DIR / f"{stem}_{run_id}_cleaned.csv"
    report_path = REPORTS_DIR / f"{stem}_{run_id}_report.pdf"
    json_path = REPORTS_DIR / f"{stem}_{run_id}_summary.json"
    artifacts = (raw_path, processed_path, report_path, json_path)

    try:
        _job_log(job_id, "Upload verified and staged.", progress=14, stage="Inspecting file")
        _job_log(job_id, "Profiling columns and missing-value patterns.", progress=24)

        def cleaner_progress(progress: int, message: str) -> None:
            mapped_progress = 24 + round(progress * 0.48)
            _job_log(
                job_id,
                message,
                progress=mapped_progress,
                stage="Cleaning dataset",
            )

        summary = cleaner_mod.clean_csv(
            str(raw_path),
            str(processed_path),
            progress_callback=cleaner_progress,
        )

        _job_log(
            job_id,
            f"Cleaning pass complete: {summary.get('cleaned_rows', 0):,} rows retained.",
            progress=72,
            stage="Building outputs",
        )
        report_mod.generate_pdf_report(
            summary, str(report_path), title=f"Summary: {original_filename}"
        )
        report_mod.save_json_summary(summary, str(json_path))

        _job_log(job_id, "CSV, PDF, and JSON outputs generated.", progress=88)
        _persist_run(
            original_filename=original_filename,
            run_id=run_id,
            user_email=user_email,
            raw_path=raw_path,
            processed_path=processed_path,
            report_path=report_path,
            json_path=json_path,
            summary=summary,
        )
        _job_log(job_id, "Run recorded securely to your workspace.", progress=97)

        return {
            "raw_file": str(raw_path.as_posix()),
            "cleaned_file": str(processed_path.as_posix()),
            "report_file": str(report_path.as_posix()),
            "json_summary": str(json_path.as_posix()),
            "summary": summary,
            "run_id": run_id,
        }
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        _remove_artifacts(artifacts)
        raise ProcessingFailure(
            "invalid_csv",
            "We could not read this CSV. Check its encoding and column structure, then try again.",
        ) from exc
    except ValueError as exc:
        _remove_artifacts(artifacts)
        raise ProcessingFailure(
            "invalid_values",
            "This CSV contains values the cleaner could not interpret. Review the source file and retry.",
        ) from exc
    except ProcessingFailure:
        _remove_artifacts(artifacts)
        raise
    except Exception as exc:
        _remove_artifacts(artifacts)
        logger.exception("Processing job %s failed", job_id)
        raise ProcessingFailure(
            "processing_failed",
            "The cleaning run stopped unexpectedly. Your original file is unchanged; please retry.",
        ) from exc


def _run_job(
    job_id: str,
    original_filename: str,
    run_id: str,
    user_email: str,
    raw_path: Path,
) -> None:
    _update_job(job_id, status="running", started_at=_utc_now())
    try:
        result = _process_saved_upload(job_id, original_filename, run_id, user_email, raw_path)
        _job_log(job_id, "Processing complete. Outputs are ready.", progress=100, stage="Complete")
        _update_job(job_id, status="complete", result=result, completed_at=_utc_now())
    except ProcessingFailure as exc:
        logger.warning("Job %s failed with %s", job_id, exc.code)
        _job_log(job_id, exc.public_message, stage="Stopped", level="error")
        _update_job(
            job_id,
            status="failed",
            error={"code": exc.code, "message": exc.public_message},
            completed_at=_utc_now(),
        )


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "logs": list(job["logs"]),
        "result": job.get("result"),
        "error": job.get("error"),
        "updated_at": job["updated_at"],
    }


@router.post("/process/start", status_code=202)
async def start_process_upload(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    file: UploadFile = File(...),
):
    """Stage a CSV and return immediately with a pollable processing job."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    _cleanup_jobs()
    original_filename = Path(file.filename).name
    run_id = uuid.uuid4().hex
    job_id = uuid.uuid4().hex
    raw_path = RAW_DIR / f"{_safe_stem(original_filename)}_{run_id}.csv"
    size = await _save_upload(file, raw_path)
    now = _utc_now()

    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "owner": current_user["email"],
            "status": "queued",
            "progress": 8,
            "stage": "Upload accepted",
            "logs": [
                {
                    "time": now,
                    "level": "info",
                    "message": f"Received {original_filename} ({size / 1024 / 1024:.1f} MB).",
                }
            ],
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
            "created_epoch": time.time(),
        }

    background_tasks.add_task(
        _run_job,
        job_id,
        original_filename,
        run_id,
        current_user["email"],
        raw_path,
    )
    return _public_job(_JOBS[job_id])


@router.get("/process/jobs/{job_id}")
def get_process_job(job_id: str, current_user: dict = Depends(get_current_user)):
    _cleanup_jobs()
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is None or job["owner"] != current_user["email"]:
            raise HTTPException(status_code=404, detail="Processing job not found")
        return _public_job(job)
