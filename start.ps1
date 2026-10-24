$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
}
if (-not (Test-Path -LiteralPath 'node_modules')) {
    npm ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Node dependency installation failed' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
npm run build
if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
Write-Host 'GridTrace: http://127.0.0.1:8000 (Ctrl+C stops the server)'
& '.\.venv\Scripts\python.exe' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
