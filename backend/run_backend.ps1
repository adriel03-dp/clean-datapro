$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $PSScriptRoot "requirements.txt"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. Create it with: py -3.11 -m venv backend\.venv"
}

& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

& $python -m uvicorn src.main:app --reload --port 8000
