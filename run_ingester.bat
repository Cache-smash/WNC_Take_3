@echo off
cd /d "%~dp0"
doppler run -- uv run python inventory_ingester.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ingester application failed with error code %ERRORLEVEL%
    pause
)
