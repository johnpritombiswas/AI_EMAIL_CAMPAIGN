$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Uvicorn = Join-Path $Backend "venv\Scripts\uvicorn.exe"

if (-not (Test-Path $Uvicorn)) {
    throw "Backend virtual environment not found at $Uvicorn"
}

Write-Host "Starting AI Email Campaign API..."
Write-Host "Open http://127.0.0.1:8000/"

Push-Location $Backend
try {
    & $Uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}
finally {
    Pop-Location
}
