$python = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$requirements = Join-Path $PSScriptRoot "requirements.txt"
$app = Join-Path $PSScriptRoot "web_app.py"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. Create it with: py -3.11 -m venv .venv"
}

& $python -m pip install -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

Push-Location $PSScriptRoot
try {
    & $python $app
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend server stopped with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
