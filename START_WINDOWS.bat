@echo off
setlocal
cd /d "%~dp0"
title Coffee Rush - The Unwritten Cafe
where py >nul 2>&1
if not errorlevel 1 (
    py -3 launch_game.py
    goto done
)
where python >nul 2>&1
if not errorlevel 1 (
    python launch_game.py
    goto done
)
echo Python 3 is not installed or not available in PATH.
echo To play now, double-click Play_Offline_Demo.html in this folder.
echo To enable shared community rankings, install Python 3 from python.org.
:done
echo.
echo If your game is not visible, try opening Play_Offline_Demo.html.
pause
