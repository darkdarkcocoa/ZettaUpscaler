@echo off
setlocal enabledelayedexpansion
title ZettaUpscaler Installer
cls

:: 색상 설정
color 0F

echo.
echo ==============================================================
echo                 ZettaUpscaler Auto Installer
echo                         Version 1.0
echo ==============================================================
echo.
echo This installer will set up everything you need for ZettaUpscaler
echo.
echo What will be installed:
echo   [*] Python 3.12 (if not already installed)
echo   [*] FFmpeg for video processing
echo   [*] Python virtual environment
echo   [*] All required packages (PyTorch, Real-ESRGAN, etc.)
echo   [*] Safe environment variables
echo.
echo --------------------------------------------------------------
echo.
echo Press any key to start installation...
pause >nul

:: 관리자 권한 체크
net session >nul 2>&1
if %errorlevel% neq 0 (
    cls
    echo.
    echo ==============================================================
    echo                     ADMINISTRATOR REQUIRED
    echo ==============================================================
    echo.
    echo   This installer needs administrator privileges.
    echo.
    echo   Please:
    echo   1. Close this window
    echo   2. Right-click install.bat
    echo   3. Select "Run as Administrator"
    echo.
    echo ==============================================================
    echo.
    pause
    exit /b 1
)

:: 현재 디렉토리 저장
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

cls
echo.
echo ==============================================================
echo                   INSTALLATION IN PROGRESS
echo ==============================================================
echo.
echo [Step 1/7] Checking Python installation...
echo --------------------------------------------------------------

:: Python 3.12 우선 확인
set "PYTHON_FOUND=0"
set "PYTHON_VERSION="

:: py launcher로 3.12 확인
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3.12 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%i in ('py -3.12 --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo   [OK] Python 3.12 found (using py launcher)
        set "PYTHON_FOUND=1"
    )
)

:: 기본 Python 확인
if "!PYTHON_FOUND!"=="0" (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo   [!] Python !PYTHON_VERSION! found
        echo       Note: Python 3.12 is recommended
        echo       Current: !PYTHON_VERSION!
        set "PYTHON_FOUND=1"
    )
)

if "!PYTHON_FOUND!"=="0" (
    echo   [X] Python is not installed
    echo.
    echo   Python 3.12 will now be downloaded and installed...
    echo.
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python-installer.exe'"
    echo.
    echo   IMPORTANT: When installing Python:
    echo   - UNCHECK "Add Python to PATH" to avoid conflicts
    echo   - The py launcher will be used instead
    echo.
    start /wait python-installer.exe
    del python-installer.exe
    echo.
    echo   [OK] Python installation completed
)

echo.
echo [Step 2/7] Installing FFmpeg...
echo --------------------------------------------------------------
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] FFmpeg is already installed
) else (
    echo   Downloading FFmpeg...
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    set "FFMPEG_DIR=C:\ffmpeg"
    
    powershell -Command "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile 'ffmpeg.zip'"
    echo   Extracting FFmpeg...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"
    
    if not exist "!FFMPEG_DIR!" mkdir "!FFMPEG_DIR!"
    for /d %%i in (ffmpeg-*) do (
        xcopy /E /Y "%%i\bin\*" "!FFMPEG_DIR!\bin\" >nul
    )
    
    :: 현재 세션에만 PATH 추가 (안전)
    set "PATH=%PATH%;!FFMPEG_DIR!\bin"
    
    :: 정리
    del ffmpeg.zip
    for /d %%i in (ffmpeg-*) do rmdir /S /Q "%%i"
    
    echo   [OK] FFmpeg installed successfully
    echo.
    echo   Note: To use FFmpeg permanently:
    echo   1. Open System Settings
    echo   2. Advanced system settings
    echo   3. Environment Variables
    echo   4. Add "!FFMPEG_DIR!\bin" to PATH
)

echo.
echo [Step 3/7] Creating Python virtual environment...
echo --------------------------------------------------------------
if exist ".venv" (
    echo.
    echo   [!] Virtual environment already exists
    echo.
    set /p REBUILD_VENV="   Rebuild it? (Y/N): "
    if /i "!REBUILD_VENV!"=="Y" (
        echo   Removing old environment...
        rmdir /S /Q .venv
        echo   Creating new environment...
        where py >nul 2>&1
        if %errorlevel% equ 0 (
            py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv || python -m venv .venv
        ) else (
            python -m venv .venv
        )
        echo   [OK] Virtual environment recreated
    ) else (
        echo   [OK] Keeping existing virtual environment
    )
) else (
    echo   Creating virtual environment...
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv || python -m venv .venv
    ) else (
        python -m venv .venv
    )
    echo   [OK] Virtual environment created
)

echo.
echo [Step 4/7] Checking GPU support...
echo --------------------------------------------------------------
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] NVIDIA GPU detected
    for /f "tokens=2 delims=:" %%i in ('nvidia-smi ^| findstr "CUDA Version"') do (
        set CUDA_VERSION=%%i
        echo       CUDA Version:!CUDA_VERSION!
    )
    set "TORCH_INDEX=https://download.pytorch.org/whl/cu121"
    set "GPU_SUPPORT=1"
) else (
    echo   [!] No NVIDIA GPU detected
    echo       Installing CPU-only version
    set "TORCH_INDEX=https://download.pytorch.org/whl/cpu"
    set "GPU_SUPPORT=0"
)

echo.
echo [Step 5/7] Installing Python packages...
echo --------------------------------------------------------------
echo   Activating virtual environment...
call .venv\Scripts\activate.bat

:: pip 업그레이드
echo   Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: PyTorch 설치
echo   Installing PyTorch... (this may take a few minutes)
if "!GPU_SUPPORT!"=="1" (
    echo   [GPU version - optimized for your NVIDIA card]
    pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
) else (
    echo   [CPU version - no GPU acceleration]
    pip install torch torchvision
)

:: 나머지 의존성 설치
echo.
echo   Installing other packages...
pip install -r requirements.txt

echo.
echo   [OK] All packages installed successfully

echo.
echo [Step 6/7] Creating launcher script...
echo --------------------------------------------------------------
:: upscaler.bat이 이미 있는지 확인
if exist upscaler.bat (
    echo   [OK] upscaler.bat already exists
) else (
    :: upscaler.bat 생성
    (
        echo @echo off
        echo setlocal
        echo set "SCRIPT_DIR=%%~dp0"
        echo cd /d "%%SCRIPT_DIR%%"
        echo.
        echo :: Use virtual environment Python
        echo set "PYTHON_EXE=%%SCRIPT_DIR%%.venv\Scripts\python.exe"
        echo.
        echo :: Check if virtual environment exists
        echo if not exist "%%PYTHON_EXE%%" ^(
        echo     echo Error: Virtual environment not found!
        echo     echo Please run install.bat first
        echo     pause
        echo     exit /b 1
        echo ^)
        echo.
        echo :: Run upscaler
        echo "%%PYTHON_EXE%%" -m upscaler %%*
    ) > upscaler.bat
    echo   [OK] upscaler.bat created
)

echo.
echo [Step 7/7] Setting up PATH helper...
echo --------------------------------------------------------------
:: PATH 추가 헬퍼 파일 생성
echo @echo off > add-to-path.bat
echo :: ZettaUpscaler PATH helper >> add-to-path.bat
echo set "PATH=%%PATH%%;%PROJECT_DIR%" >> add-to-path.bat
echo echo ZettaUpscaler has been added to PATH for this session. >> add-to-path.bat
echo echo You can now use 'upscaler' from anywhere! >> add-to-path.bat

echo   [OK] add-to-path.bat created
echo.
echo   TIP: Run 'add-to-path.bat' in any new command prompt
echo        to use 'upscaler' command from anywhere.

echo.
echo ==============================================================
echo                    OPTIONAL: Download Models
echo ==============================================================
echo.
echo   AI models will be downloaded automatically on first use.
echo   Or you can download them now (recommended).
echo.
set /p DOWNLOAD_MODELS="   Download models now? (Y/N): "

if /i "!DOWNLOAD_MODELS!"=="Y" (
    echo.
    echo   Downloading models...
    call .venv\Scripts\activate.bat
    python -m upscaler models --download realesr-general-x4v3
    python -m upscaler models --download realesrgan-x4plus
    echo.
    echo   [OK] Models downloaded
)

cls
echo.
echo ==============================================================
echo                  INSTALLATION COMPLETED!
echo ==============================================================
echo.
echo   ZettaUpscaler has been successfully installed.
echo.
echo   HOW TO USE:
echo.
echo   Option 1 - From this folder:
echo     .\upscaler image input.jpg output.jpg --scale 4
echo     .\upscaler video input.mp4 output.mp4 --scale 4
echo.
echo   Option 2 - From anywhere (recommended):
echo     1. Open a new command prompt
echo     2. Run: add-to-path.bat
echo     3. Use: upscaler image photo.jpg photo_4k.jpg
echo.
echo   Quick commands:
echo     upscaler --help    (show help)
echo     upscaler doctor    (check system)
echo.
echo ==============================================================
echo.
echo Press any key to exit...
pause >nul