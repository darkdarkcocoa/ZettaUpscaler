@echo off
setlocal
title ZettaUpscaler Updater

cls
echo.
echo ==============================================================
echo                   ZettaUpscaler Update Tool
echo ==============================================================
echo.
echo This tool will:
echo   1. Pull latest changes from GitHub
echo   2. Update all Python dependencies
echo   3. Verify installation
echo.
echo --------------------------------------------------------------
echo.

:: Check if .venv exists
if not exist ".venv\Scripts\python.exe" (
    color 0C
    echo ERROR: Virtual environment not found!
    echo Please run install.bat first.
    echo.
    pause
    exit /b 1
)

:: Pull latest changes
echo [1/3] Pulling latest changes from GitHub...
echo --------------------------------------------------------------
git pull
if %ERRORLEVEL% NEQ 0 (
    color 0E
    echo.
    echo WARNING: Git pull failed or no changes available.
    echo Continuing with dependency update...
    echo.
)

:: Update dependencies
echo.
echo [2/3] Updating Python dependencies...
echo --------------------------------------------------------------
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt --upgrade
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo ERROR: Failed to update dependencies!
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

:: Verify installation
echo.
echo [3/3] Verifying installation...
echo --------------------------------------------------------------
.venv\Scripts\python.exe -m upscaler doctor
if %ERRORLEVEL% NEQ 0 (
    color 0E
    echo.
    echo WARNING: Verification failed. Some features may not work properly.
    echo.
) else (
    color 0A
    echo.
    echo ==============================================================
    echo                    UPDATE SUCCESSFUL!
    echo ==============================================================
    echo.
    echo What's new:
    echo   - Beautiful Rich UI with progress bars
    echo   - Batch processing with 'upscale all'
    echo   - Better Windows Terminal integration
    echo   - Performance improvements
    echo.
    echo Try the new batch processing:
    echo   upscale all --dry-run
    echo.
)

echo.
pause