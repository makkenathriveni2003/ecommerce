@echo off
echo ======================================================================
echo           ShopZone Day 25 Capstone Final Project - Automated Tests    
echo ======================================================================

set SCRIPT_DIR=%~dp0
set REPO_ROOT=%SCRIPT_DIR%..
set PYTHON_CMD=%REPO_ROOT%\.venv\Scripts\python.exe
if not exist "%PYTHON_CMD%" set PYTHON_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe
if not exist "%PYTHON_CMD%" set PYTHON_CMD=python

"%PYTHON_CMD%" "%SCRIPT_DIR%scripts\run_day25_tests.py"
