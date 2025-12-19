"""
Modern Flask-based web interface for CleanDataPro.
Alternative to Streamlit with more control over UI/UX.

Run with: python web_app.py
Then visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import pandas as pd
import requests
import json
import os
from pathlib import Path
from datetime import datetime
import io

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "cleandatapro_secret_key_2024"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB max file size
app.config["UPLOAD_FOLDER"] = "temp_uploads"

BACKEND_BASE = os.environ.get("CLEAN_DATAPRO_BACKEND", "http://localhost:8000")

# Ensure upload folder exists
Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

# Store processing results in session
processing_results = {}


@app.route("/")
def index():
    """Home page"""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle file upload and return preview"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400
    
    try:
        filename = secure_filename(file.filename)
        df = pd.read_csv(file)
        
        # Store in session for later processing
        session["current_file"] = filename
        session["file_shape"] = df.shape
        session.modified = True
        
        return jsonify({
            "success": True,
            "filename": filename,
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "preview": df.head(10).to_dict(orient="records"),
            "missing_summary": {
                col: {
                    "count": int(df[col].isna().sum()),
                    "pct": round((df[col].isna().sum() / len(df)) * 100, 2)
                }
                for col in df.columns
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/process", methods=["POST"])
def process():
    """Process file with backend"""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    
    try:
        # Call backend API
        files = {"file": (file.filename, file.getvalue(), "text/csv")}
        resp = requests.post(f"{BACKEND_BASE}/api/process", files=files, timeout=60)
        
        if resp.status_code != 200:
            return jsonify({"error": f"Backend error: {resp.text}"}), 500
        
        result = resp.json()
        
        # Store result for downloads
        session["last_result"] = result
        session.modified = True
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Cannot connect to backend. Is the FastAPI server running on http://localhost:8000?"
        }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history", methods=["GET"])
def get_history():
    """Fetch processing history from backend"""
    try:
        resp = requests.get(f"{BACKEND_BASE}/api/runs?limit=50", timeout=10)
        if resp.status_code == 200:
            return jsonify(resp.json())
        else:
            return jsonify({"error": "Failed to fetch history"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/test-backend", methods=["GET"])
def test_backend():
    """Test backend connection"""
    try:
        resp = requests.get(f"{BACKEND_BASE}/api/runs?limit=1", timeout=5)
        if resp.status_code == 200:
            return jsonify({"success": True, "message": "Backend is online"})
        else:
            return jsonify({
                "success": False,
                "message": f"Backend returned status {resp.status_code}"
            }), 500
    except requests.exceptions.ConnectionError:
        return jsonify({
            "success": False,
            "message": "Cannot connect to backend"
        }), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/download/<kind>/<filename>", methods=["GET"])
def download_file(kind, filename):
    """Download file from backend"""
    try:
        url = f"{BACKEND_BASE}/api/download?kind={kind}&filename={filename}"
        resp = requests.get(url, timeout=30)
        
        if resp.status_code == 200:
            return send_file(
                io.BytesIO(resp.content),
                mimetype=resp.headers.get("content-type", "application/octet-stream"),
                as_attachment=True,
                download_name=filename
            )
        else:
            return jsonify({"error": "File not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 Starting CleanDataPro Web Interface...")
    print("📍 Open http://localhost:5000 in your browser")
    print("⚠️  Make sure FastAPI backend is running on http://localhost:8000")
    app.run(debug=True, port=5000)
