@echo off
rem Double-click from the repository root.
cd /d "%~dp0WsnLocalization2026"
if not exist "run_demo.bat" (
    echo Could not find WsnLocalization2026\run_demo.bat
    pause
    exit /b 1
)
call run_demo.bat
