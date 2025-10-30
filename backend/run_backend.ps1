# Activate virtualenv (assumes .venv in backend/) and run uvicorn
if (-Not (Test-Path -Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtualenv not found in backend/.venv. Create one with: python -m venv .venv" -ForegroundColor Yellow
}
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
