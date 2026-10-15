# PowerShell test runner for Day 22: AI Focus Project
$ErrorActionPreference = "Stop"

Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "  DAY 22: AI FOCUS PROJECT - TEST RUNNER (PowerShell)" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "`n[1/3] Running Backend Day 22 Pytest Suite..." -ForegroundColor Yellow
& ".venv\Scripts\pytest.exe" backend/tests/test_day22_ai_focus.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Backend tests failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[2/3] Running Complete Day 22 Automated Verification..." -ForegroundColor Yellow
& ".venv\Scripts\python.exe" day22/run_day22_tests.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Verification checks failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[3/3] Running Frontend AI Component Vitest Tests..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\frontend"
& "npm.cmd" test -- src/pages/AiAssistant.test.tsx src/hooks/useWebSocket.test.ts src/components/LiveChatWidget.test.tsx --run
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Frontend tests failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Set-Location $ProjectRoot
Write-Host "`n===========================================================================" -ForegroundColor Green
Write-Host "  ALL DAY 22 BACKEND & FRONTEND TESTS PASSED (100%)!" -ForegroundColor Green
Write-Host "===========================================================================`n" -ForegroundColor Green
