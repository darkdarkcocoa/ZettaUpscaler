@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "ORIGINAL_DIR=%CD%"

:: 가상환경 Python 경로를 정확히 지정 (따옴표 중요!)
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

:: 가상환경 Python이 있는지 확인
if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

:: upscaler 실행 (원래 디렉토리를 환경변수로 전달)
set "UPSCALER_ORIGINAL_DIR=%ORIGINAL_DIR%"
cd /d "%SCRIPT_DIR%"
"%PYTHON_EXE%" -m upscaler %*