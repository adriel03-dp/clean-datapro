# CleanDataPro Backend

This folder contains a FastAPI-based backend for the CleanDataPro project.

Quick start (local):

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Run the app

From the repository root (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r backend\requirements.txt
\.venv\Scripts\python.exe -m uvicorn backend.src.main:app --reload --port 8000
```

Or if you `cd` into the `backend` folder first:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
\.venv\Scripts\python.exe -m uvicorn src.main:app --reload --port 8000
```

## Troubleshooting

- "uvicorn" not found: make sure the venv is activated and `uvicorn` is installed in that environment (install via `pip install -r requirements.txt`).
- "Address already in use" when binding to port 8000: another process is using that port. Find and stop it or run the server on a different port, e.g.: `--port 8001`.
- If the app fails to import `backend.src.main`, run from repository root and use the module path `backend.src.main:app` (or `src.main:app` when running from inside `backend/`).

Endpoints:

- POST /api/process - accepts a CSV file (multipart/form-data) and returns cleaning artifacts and a JSON summary.
- GET /healthz - health check

## Environment

The backend reads environment variables from a `.env` file in the `backend/` folder. Create a `backend/.env` file with at least:

```
MONGODB_URI=
```

If you plan to use MongoDB features, set `MONGODB_URI` to your connection string (for MongoDB Atlas or local instance). The project uses `python-dotenv` to load the file.
