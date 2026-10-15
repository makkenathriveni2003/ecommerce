@echo off
echo ===========================================================================
echo  DAY 22: AI FOCUS PROJECT - TEST RUNNER
echo ===========================================================================
cd /d "%~dp0\.."

echo [1/2] Running Backend AI Focus Pytest Suite...
.venv\Scripts\pytest.exe backend\tests\test_day22_ai_focus.py -v
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend tests failed.
    exit /b %ERRORLEVEL%
)

echo [2/2] Running Complete Day 22 Automated Verification...
.venv\Scripts\python.exe day22\run_day22_tests.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Day 22 Verification failed.
    exit /b %ERRORLEVEL%
)

echo ===========================================================================
echo  ALL DAY 22 TESTS PASSED SUCCESSFULLY!
echo ===========================================================================
pause
