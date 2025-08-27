@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 가상환경 Python 경로를 정확히 지정 (따옴표 중요!)
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

:: 가상환경 Python이 있는지 확인
if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Python 버전 확인 (디버깅용)
echo Using Python: %PYTHON_EXE%
"%PYTHON_EXE%" --version

:: upscaler 실행
"%PYTHON_EXE%" -m upscaler %*