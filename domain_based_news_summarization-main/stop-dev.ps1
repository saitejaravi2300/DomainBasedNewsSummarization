#!/usr/bin/env pwsh

$ErrorActionPreference = "SilentlyContinue"

function Stop-PortProcess {
	param([int]$Port)
	$conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
	if ($null -ne $conn) {
		Stop-Process -Id $conn.OwningProcess -Force
		Write-Host "Stopped process on port $Port (PID=$($conn.OwningProcess))." -ForegroundColor Yellow
	} else {
		Write-Host "No listening process on port $Port." -ForegroundColor DarkGray
	}
}

Write-Host "Stopping backend/frontend by port..." -ForegroundColor Cyan
Stop-PortProcess -Port 8000
Stop-PortProcess -Port 3000

Write-Host "Done." -ForegroundColor Green
