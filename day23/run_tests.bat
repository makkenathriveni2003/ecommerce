@echo off
echo ======================================================================
echo          ShopZone Day 23 DevOps / AWS Focus - Automated Tests
echo ======================================================================

set PYTHON_CMD=..\.venv\Scripts\python.exe
if not exist "%PYTHON_CMD%" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)
if not exist "%PYTHON_CMD%" (
    set PYTHON_CMD=python
)

"%PYTHON_CMD%" scripts\run_day23_tests.py
pause
