"""
Modern Flask-based web interface for CleanDataPro.
Alternative to Streamlit with more control over UI/UX.

Run with: python web_app.py
Then visit: http://localhost:5000
"""

import os
import secrets

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import pandas as pd
import requests
from pathlib import Path
import io

from config import BACKEND_BASE

PLACEHOLDER_VALUES = {
    "unknown", "n/a", "na", "nan", "none", "null", "error", "missing",
    "undefined", "unavailable", "", "-", "--", "?", "n.a.", "#n/a",
}


def _preview_missing_summary(df):
    """Calculate preview quality counts with vectorized pandas operations."""
    summary = {}
    row_count = len(df)
    for column in df.columns:
        series = df[column]
        mask = series.isna()
        if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
            normalized = series.astype("string").str.strip().str.lower()
            mask = mask | normalized.isin(PLACEHOLDER_VALUES)
        count = int(mask.sum())
        summary[column] = {
            "count": count,
            "pct": round((count / row_count) * 100, 2) if row_count else 0,
        }
    return summary

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not app.secret_key:
    if os.environ.get("RENDER") or os.environ.get("ENVIRONMENT", "").lower() == "production":
        raise RuntimeError("FLASK_SECRET_KEY must be configured in production")
    app.secret_key = secrets.token_urlsafe(32)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size
app.config["UPLOAD_FOLDER"] = "temp_uploads"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = bool(
    os.environ.get("RENDER") or os.environ.get("ENVIRONMENT", "").lower() == "production"
)


@app.errorhandler(413)
def request_entity_too_large(_error):
    return jsonify({"error": "CSV file is larger than 100 MB."}), 413

# Ensure upload folder exists
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)


@app.get("/favicon.ico")
def favicon():
    """Serve the same lightweight brand mark for browsers requesting ICO."""
    return send_file(
        Path(app.static_folder) / "favicon.svg", mimetype="image/svg+xml"
    )

@app.route("/")
def index():
    """Home page"""
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return render_template(
        "index.html",
        backend_url=BACKEND_BASE,
        authenticated=bool(session.get("token")),
        user_name=session.get("name", ""),
        user_email=session.get("email", ""),
        csrf_token=session["csrf_token"],
    )


def _auth_headers():
    token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _require_session():
    if not session.get("token"):
        return jsonify({"error": "Authentication required"}), 401
    return None


@app.before_request
def protect_state_changing_requests():
    """Require the token rendered into the page for cookie-backed POSTs."""
    if request.method != "POST" or not request.path.startswith("/api/"):
        return None
    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRFToken")
    if not expected or not supplied or not secrets.compare_digest(expected, supplied):
        return jsonify({"error": "Invalid security token. Refresh the page and try again."}), 400
    return None


def _proxy_auth(endpoint, payload):
    try:
        response = requests.post(
            f"{BACKEND_BASE}{endpoint}", json=payload, timeout=(10, 90)
        )
        data = response.json()
    except requests.RequestException:
        return jsonify({"error": "The backend is waking up or unavailable. Try again shortly."}), 503
    except ValueError:
        return jsonify({"error": "The backend returned an invalid response."}), 502

    if response.status_code >= 400:
        return jsonify({"error": data.get("detail", data.get("message", "Authentication failed."))}), response.status_code

    session["token"] = data.get("token")
    session["email"] = data.get("email", payload.get("email", ""))
    session["name"] = data.get("name", payload.get("name", ""))
    return jsonify({"success": True, "email": session["email"], "name": session["name"]})


@app.post("/api/auth/login")
def login():
    return _proxy_auth("/api/auth/login", request.get_json(silent=True) or {})


@app.post("/api/auth/register")
def register():
    return _proxy_auth("/api/auth/register", request.get_json(silent=True) or {})


@app.get("/api/auth/session")
def auth_session():
    if not session.get("token"):
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "email": session.get("email", ""),
        "name": session.get("name", ""),
    })


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file upload and return preview"""
    denied = _require_session()
    if denied:
        return denied
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400
    
    try:
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "Please choose a valid filename."}), 400
        df = pd.read_csv(file, keep_default_na=False, low_memory=False)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "preview": df.head(10).to_dict(orient="records"),
            "missing_summary": _preview_missing_summary(df),
        })
    
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        return jsonify({"error": "The uploaded file is not a readable CSV."}), 400
    except Exception:
        app.logger.exception("Unable to build CSV preview")
        return jsonify({"error": "Unable to preview this CSV."}), 500


def _public_processing_error(response, fallback):
    """Return a production-safe message without exposing backend internals."""
    if response.status_code in (400, 413):
        try:
            detail = response.json().get("detail")
            if isinstance(detail, str) and detail:
                return detail
        except ValueError:
            pass
    if response.status_code in (401, 403):
        return "Your session has expired. Sign in again and retry."
    return fallback


@app.post("/api/process/start")
def start_process():
    """Stage a file with the backend and return its background job."""
    denied = _require_session()
    if denied:
        return denied
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400
    
    try:
        # Call backend API
        # Large uploads are spooled to a temporary file by Werkzeug; that
        # stream does not reliably expose BytesIO.getvalue(). Read from the
        # stream explicitly so both small and large CSVs work.
        file.stream.seek(0)
        payload = file.stream.read()
        files = {"file": (file.filename, payload, "text/csv")}
        resp = requests.post(
            f"{BACKEND_BASE}/api/process/start",
            files=files,
            headers=_auth_headers(),
            timeout=(15, 120),
        )
        if resp.status_code != 202:
            message = _public_processing_error(
                resp, "The processing service could not start this run. Please retry."
            )
            app.logger.warning("Processing start failed with status %s", resp.status_code)
            return jsonify({"error": message}), resp.status_code
        return jsonify(resp.json()), 202
    except requests.exceptions.Timeout:
        return jsonify({"error": "The upload took too long. Check your connection and retry."}), 504
    except requests.exceptions.RequestException:
        app.logger.exception("Unable to reach processing service")
        return jsonify({"error": "The processing service is temporarily unavailable."}), 503
    except ValueError:
        app.logger.exception("Processing service returned malformed JSON")
        return jsonify({"error": "The processing service returned an invalid response."}), 502
    except Exception:
        app.logger.exception("Unexpected error while starting CSV processing")
        return jsonify({"error": "The cleaning run could not be started. Please retry."}), 500


@app.get("/api/process/status/<job_id>")
def process_status(job_id):
    """Proxy authenticated job status without exposing server exceptions."""
    denied = _require_session()
    if denied:
        return denied
    try:
        resp = requests.get(
            f"{BACKEND_BASE}/api/process/jobs/{job_id}",
            headers=_auth_headers(),
            timeout=(10, 30),
        )
        if resp.status_code != 200:
            message = _public_processing_error(
                resp, "The cleaning status is temporarily unavailable. Please retry."
            )
            return jsonify({"error": message}), resp.status_code
        return jsonify(resp.json())
    except requests.exceptions.RequestException:
        app.logger.exception("Unable to poll processing job %s", job_id)
        return jsonify({"error": "The cleaning status is temporarily unavailable."}), 503
    except ValueError:
        app.logger.exception("Malformed processing status for job %s", job_id)
        return jsonify({"error": "The processing service returned an invalid response."}), 502


@app.route("/api/history", methods=["GET"])
def get_history():
    """Fetch processing history from backend"""
    denied = _require_session()
    if denied:
        return denied
    try:
        resp = requests.get(
            f"{BACKEND_BASE}/api/runs?limit=50", headers=_auth_headers(), timeout=15
        )
        if resp.status_code == 200:
            return jsonify(resp.json())
        if resp.status_code in (401, 403):
            session.clear()
            return jsonify({"error": "Your session has expired. Please sign in again."}), 401
        return jsonify({"error": "History service unavailable"}), resp.status_code
    except requests.RequestException:
        return jsonify({"error": "History service is temporarily unavailable."}), 503


@app.route("/api/test-backend", methods=["GET"])
def test_backend():
    """Test backend connection"""
    try:
        resp = requests.get(f"{BACKEND_BASE}/healthz", timeout=5)
        if resp.status_code == 200:
            return jsonify({"success": True, "message": "Backend is online"})
        app.logger.warning("Backend health check returned %s", resp.status_code)
        return jsonify({
            "success": False,
            "message": "The processing service is temporarily unavailable."
        }), 503
    except requests.exceptions.RequestException:
        app.logger.exception("Backend health check failed")
        return jsonify({
            "success": False,
            "message": "The processing service is temporarily unavailable."
        }), 503


@app.route("/download/<kind>/<filename>", methods=["GET"])
def download_file(kind, filename):
    """Download file from backend"""
    denied = _require_session()
    if denied:
        return denied
    try:
        resp = requests.get(
            f"{BACKEND_BASE}/api/download",
            params={"kind": kind, "filename": filename},
            headers=_auth_headers(),
            timeout=30,
        )
        
        if resp.status_code == 200:
            return send_file(
                io.BytesIO(resp.content),
                mimetype=resp.headers.get("content-type", "application/octet-stream"),
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({"error": "File not found or access denied"}), resp.status_code
    
    except requests.RequestException:
        return jsonify({"error": "Download service is temporarily unavailable."}), 503


if __name__ == "__main__":
    print("🚀 Starting CleanDataPro Web Interface...")
    print("📍 Open http://localhost:5000 in your browser")
    print("⚠️  Make sure FastAPI backend is running on http://localhost:8000")
    app.run(debug=True, port=5000)
