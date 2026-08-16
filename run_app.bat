@echo off
cd /d "%~dp0"
title WNC Take 3 - Listing Studio
doppler run -- uv run python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Script failed with error code %ERRORLEVEL%
    pause
)
