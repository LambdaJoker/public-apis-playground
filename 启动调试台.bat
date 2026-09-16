@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Public APIs Playground
echo ============================================================
echo  Public APIs Playground - local server + proxy
echo  A browser window will open automatically.
echo  Keep this window open while using the playground.
echo  Press Ctrl + C here to stop the server.
echo ============================================================
echo.

python serve.py 8899
if errorlevel 1 py -3 serve.py 8899
if errorlevel 1 (
  echo.
  echo [ERROR] Python not found in PATH.
  echo Please install Python 3.8+ from https://www.python.org/downloads/
  echo or run this manually:  python serve.py
  echo.
  pause
)
