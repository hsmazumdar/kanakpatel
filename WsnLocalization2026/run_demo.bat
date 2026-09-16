@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title GPS-Denied Direction-Aware Routing — reviewer launcher
color 0A

set "PYTHONIOENCODING=utf-8"
set "MPLBACKEND=TkAgg"

call :find_python
if not defined PY (
    echo.
    echo Could not find Python 3.
    echo Install Python 3.9+ from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

:menu
cls
echo ============================================================
echo  GPS-Denied Direction-Aware Routing
echo  Reviewer launcher
echo ============================================================
echo  Python: %PY%
echo  Folder: %CD%
echo.
echo    1  Visual demo  (new source/destination each trial)
echo    2  Console GPS-denied demo
echo    3  Install Python requirements
echo    4  Reproduce main routing tables/figures
echo    5  Void stress test (greedy around a hole)
echo    6  Open Results folder
echo    7  Exit
echo.
echo  Tip: option 1 opens an animation window. Close it to return here.
echo ============================================================
echo.

set "CHOICE="
set /p CHOICE="Select [1]: "
if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="1" goto visual
if "%CHOICE%"=="2" goto console
if "%CHOICE%"=="3" goto install
if "%CHOICE%"=="4" goto routing
if "%CHOICE%"=="5" goto voids
if "%CHOICE%"=="6" goto results
if "%CHOICE%"=="7" goto end
if /I "%CHOICE%"=="q" goto end
echo Unknown choice.
pause
goto menu

:visual
echo.
echo Starting visual demo: 8 packets, a new src/dst each trial...
echo Close the plot window when finished.
echo.
%PY% demo\dynamic_gps_denied_routing.py --n 80 --trials 8
if errorlevel 1 (
    echo.
    echo Demo failed. If matplotlib is missing, choose option 3 first.
)
echo.
pause
goto menu

:console
echo.
%PY% experiments\gps_denied_demo.py
echo.
pause
goto menu

:install
echo.
echo Installing requirements...
%PY% -m pip install -r requirements.txt
echo.
pause
goto menu

:routing
echo.
echo Reproducing N=250 routing comparison. This can take a few minutes.
echo Command: experiments\routing_reference_vs_relative.py --seeds 20 --pairs 500
echo.
%PY% experiments\routing_reference_vs_relative.py --seeds 20 --pairs 500
echo.
pause
goto menu

:voids
echo.
echo Communication-void routing. This can take about a minute.
echo.
%PY% experiments\routing_voids.py --seeds 10 --pairs 300 --n 250
echo.
pause
goto menu

:results
if exist "Results\" (
    start "" explorer "%CD%\Results"
) else (
    echo Results folder not found.
    pause
)
goto menu

:find_python
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY=py -3"
        exit /b 0
    )
)
where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY=python"
        exit /b 0
    )
)
where python3 >nul 2>&1
if not errorlevel 1 (
    python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PY=python3"
        exit /b 0
    )
)
exit /b 1

:end
endlocal
exit /b 0
