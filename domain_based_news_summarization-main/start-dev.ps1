#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

Write-Host "[1/2] Starting backend locally on http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$backendDir'; uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
)

Write-Host "[2/2] Starting frontend locally on http://localhost:3000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$frontendDir'; pnpm run dev"
)

Write-Host "Done. Full stack is running locally (MongoDB Atlas configured via backend/.env)." -ForegroundColor Green
Write-Host "Tip: run ./stop-dev.ps1 to stop local ports." -ForegroundColor Yellow
