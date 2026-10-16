Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "          ShopZone Day 25 Capstone Final Project - Automated Tests    " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$repoRoot = (Resolve-Path "$scriptDir\..").Path

$pythonCmd = "$repoRoot\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = "$scriptDir\.venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = "python"
}

$targetScript = "$scriptDir\scripts\run_day25_tests.py"
& $pythonCmd $targetScript
