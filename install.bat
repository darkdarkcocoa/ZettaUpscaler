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
echo [Step 1/8] Checking Python installation...
echo --------------------------------------------------------------

:: Python 3.12 우선 확인
set "PYTHON_FOUND=0"
set "PYTHON_VERSION="
set "PYTHON_MAJOR=0"
set "PYTHON_MINOR=0"

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
        
        :: Python 3.10+ 호환성 경고
        for /f "tokens=1-2 delims=." %%a in ("!PYTHON_VERSION!") do (
            set /a PYTHON_MINOR=%%b
            if !PYTHON_MINOR! geq 10 (
                echo       [WARNING] Python 3.10+ may have compatibility issues
                echo       Recommended: Python 3.8 or 3.9
            )
        )
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
echo [Step 2/8] Installing FFmpeg...
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
echo [Step 3/8] Checking Visual Studio Build Tools...
echo --------------------------------------------------------------
:: Visual Studio Build Tools 체크 (Windows에서 basicsr 빌드 필요)
where cl >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Visual Studio Build Tools detected
) else (
    echo   [WARNING] Visual Studio Build Tools not found
    echo   Some packages may fail to install without it.
    echo   
    echo   To install:
    echo   1. Download Visual Studio 2019/2022 Community
    echo   2. Select "Desktop development with C++" workload
    echo.
)

echo.
echo [Step 4/8] Creating Python virtual environment...
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
echo [Step 5/8] Checking GPU support...
echo --------------------------------------------------------------

:: GPU 감지 시작 (더 간단하게)
set GPU_FOUND=NO

:: nvidia-smi 테스트
nvidia-smi >nul 2>&1
if !errorlevel! equ 0 (
    set GPU_FOUND=YES
    echo   [OK] NVIDIA GPU detected!
    
    :: GPU 이름 가져오기 (옵션)
    set "GPU_NAME=NVIDIA GPU"
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu^=name --format^=csv^,noheader 2^>nul') do (
        set "GPU_NAME=%%i"
    )
    echo       GPU: !GPU_NAME!
    
    :: 4090 체크
    echo !GPU_NAME! | findstr /i "4090" >nul && (
        echo       [!] RTX 4090 detected - using optimized settings
        set "IS_4090=1"
    )
)

:: WMI 폴백 (nvidia-smi 실패시)
if "!GPU_FOUND!"=="NO" (
    echo   nvidia-smi failed, checking Windows devices...
    wmic path win32_VideoController get name | findstr /i "nvidia" >nul 2>&1
    if !errorlevel! equ 0 (
        set GPU_FOUND=YES
        echo   [OK] NVIDIA GPU found via Windows
    )
)

:: 최종 체크
if "!GPU_FOUND!"=="YES" (
    echo   [PASS] GPU check passed - continuing installation
    set "TORCH_INDEX=https://download.pytorch.org/whl/cu121"
) else (
    echo   [ERROR] No NVIDIA GPU detected!
    echo.
    echo   This application requires an NVIDIA GPU to run.
    echo   Please ensure you have NVIDIA GPU and drivers installed.
    echo.
    pause
    exit /b 1
)

echo.
echo [Step 6/8] Installing Python packages...
echo --------------------------------------------------------------
echo   Activating virtual environment...
call .venv\Scripts\activate.bat

:: pip 업그레이드
echo   Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

:: STEP 1: PyTorch GPU 버전 설치 (requirements.txt보다 먼저!)
:: CRITICAL: Must install PyTorch BEFORE requirements.txt to prevent CPU version override
echo   Installing PyTorch... (this may take a few minutes)
echo   [GPU version - optimized for your NVIDIA card]

echo   Installing PyTorch with CUDA 12.1 support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
if %errorlevel% neq 0 (
    echo.
    echo   [WARNING] CUDA 12.1 installation failed, trying CUDA 11.8...
    pip install torch==2.2.0+cu118 torchvision==0.17.0+cu118 torchaudio==2.2.0+cu118 --index-url https://download.pytorch.org/whl/cu118
    if %errorlevel% neq 0 (
        echo.
        echo   [ERROR] PyTorch GPU installation failed!
        echo.
        echo   This could be due to:
        echo   1. Network connection issues - check your internet
        echo   2. Incompatible CUDA version - update your NVIDIA drivers
        echo   3. Python version mismatch - ensure Python 3.10-3.12 is used
        echo.
        echo   Error details above. Please screenshot and share with IT support.
        echo.
        pause
        exit /b 1
    )
)

:: STEP 2: numpy 설치 (PyTorch와 호환되는 버전)
echo.
echo   Installing numpy (compatible version)...
pip install numpy==1.26.4 --no-cache-dir

:: STEP 3: 나머지 패키지 설치 (torch 제외된 requirements.txt)
echo.
echo   Installing other packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo   [WARNING] Some packages may have failed to install
)

:: STEP 4: PyTorch GPU 버전 최종 확인 (requirements.txt 설치 후)
echo.
echo   Verifying PyTorch GPU installation...
python -c "import torch; print(f'  PyTorch {torch.__version__} installed successfully')" 2>nul
if %errorlevel% neq 0 (
    echo   [ERROR] PyTorch import failed!
    pause
    exit /b 1
)

:: CUDA 사용 가능 여부 확인 (가장 중요!)
python -c "import torch; cuda_available = torch.cuda.is_available(); print(f'  CUDA Available: {cuda_available}'); exit(0 if cuda_available else 1)" 2>nul
if %errorlevel% neq 0 (
    echo   [ERROR] GPU detected but CUDA not available in PyTorch!
    echo.
    echo   This usually means PyTorch was overridden with CPU version.
    echo   Please check requirements.txt doesn't contain torch/torchvision.
    echo.
    pause
    exit /b 1
)

:: basicsr/realesrgan 설치 확인 및 재시도
echo.
echo   Verifying AI packages installation...
python -c "import basicsr" 2>nul
if %errorlevel% neq 0 (
    echo   [!] basicsr not installed properly, retrying...
    pip install basicsr --no-cache-dir --force-reinstall
)

python -c "import realesrgan" 2>nul
if %errorlevel% neq 0 (
    echo   [!] realesrgan not installed properly, retrying...
    pip install realesrgan --no-cache-dir --force-reinstall
)

:: 최종 확인
python -c "import basicsr, realesrgan; print('  [OK] AI packages verified')" 2>nul
if %errorlevel% neq 0 (
    echo   [WARNING] AI packages installation issues detected
    echo   You may experience limited functionality
) else (
    echo   [OK] All packages installed successfully
)

:: upscaler 패키지 설치
echo.
echo   Installing upscaler package...
pip install -e .
if %errorlevel% neq 0 (
    echo   [ERROR] Failed to install upscaler package!
    pause
    exit /b 1
)

echo.
echo [Step 7/8] Creating launcher script...
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
echo [Step 8/8] Setting up PATH helper...
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
:: 설치 검증
echo.
echo   Running quick test...
python -m upscaler doctor >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Installation verified!
) else (
    echo   [WARNING] Installation may have issues. Run 'upscaler doctor' for details.
)

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