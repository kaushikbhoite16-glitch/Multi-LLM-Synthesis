Write-Host "Starting Multi-LLM Synthesis Platform..." -ForegroundColor Cyan

# 1. Ensure backend .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "[INFO] Copying .env.example → backend\.env" -ForegroundColor Yellow
    Copy-Item ".env.example" "backend\.env"
}

# 2. Start backend (background job)
Write-Host "[BACKEND] Starting FastAPI on http://localhost:8000 ..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location "c:\LLM\backend"
    & "c:\LLM\backend\venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000 --reload
}

# 3. Wait briefly for backend to start
Start-Sleep -Seconds 4

# 4. Start frontend (background job)
Write-Host "[FRONTEND] Starting Vite dev server on http://localhost:5173 ..." -ForegroundColor Green
$frontendJob = Start-Job -ScriptBlock {
    $env:PATH = "C:\LLM\tools\node;$env:PATH"
    Set-Location "c:\LLM\frontend"
    & "C:\LLM\tools\node\npm.cmd" run dev
}

Write-Host ""
Write-Host "==============================" -ForegroundColor Cyan
Write-Host " System started successfully!" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Cyan
Write-Host " Frontend : http://localhost:5173" -ForegroundColor White
Write-Host " API      : http://localhost:8000" -ForegroundColor White
Write-Host " API Docs : http://localhost:8000/docs" -ForegroundColor White
Write-Host " Health   : http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers." -ForegroundColor Gray

# Keep alive and stream job output
try {
    while ($true) {
        Receive-Job -Job $backendJob 2>$null | ForEach-Object { Write-Host "[BACK] $_" -ForegroundColor DarkGray }
        Receive-Job -Job $frontendJob 2>$null | ForEach-Object { Write-Host "[FRONT] $_" -ForegroundColor DarkGray }
        Start-Sleep -Seconds 1
    }
} finally {
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    Write-Host "Servers stopped." -ForegroundColor Yellow
}
