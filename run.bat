@echo off
title AI Gym Trainer
cd /d "%~dp0"

echo Starting AI Gym Trainer...
if exist ".venv310\Scripts\python.exe" (
    ".venv310\Scripts\python.exe" main.py
) else (
    python main.py
)
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
