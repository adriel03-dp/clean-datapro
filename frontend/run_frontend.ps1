# Activate virtualenv for frontend demo and run Streamlit
if (-Not (Test-Path -Path ".venv-front\Scripts\Activate.ps1")) {
    Write-Host "Virtualenv not found in frontend/.venv-front. Create one with: python -m venv .venv-front" -ForegroundColor Yellow
}
. .\.venv-front\Scripts\Activate.ps1
pip install -r frontend\requirements.txt
streamlit run frontend\streamlit_app.py
