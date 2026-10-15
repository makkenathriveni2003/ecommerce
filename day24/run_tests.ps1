Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          ShopZone Day 24 DevOps / AWS Focus - Automated Tests        " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$pythonCmd = "..\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = "python"
}

& $pythonCmd scripts\run_day24_tests.py
