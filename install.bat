@echo off
setlocal enabledelayedexpansion
chcp 65001 > nul
cls

echo ╔══════════════════════════════════════════════════════════════╗
echo ║          🚀 ZettaUpscaler 자동 설치 프로그램                 ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 이 스크립트는 ZettaUpscaler 사용에 필요한 모든 것을 자동으로 설치합니다.
echo.
echo 설치될 항목:
echo   ✓ Python 3.12 (설치되지 않은 경우)
echo   ✓ FFmpeg
echo   ✓ Python 가상환경
echo   ✓ 모든 의존성 패키지
echo   ✓ 환경변수 설정
echo.
pause

:: 관리자 권한 체크
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  관리자 권한이 필요합니다!
    echo    스크립트를 마우스 오른쪽 클릭 → "관리자로 실행"을 선택하세요.
    pause
    exit /b 1
)

:: 현재 디렉토리 저장
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo.
echo [1/7] Python 설치 확인 중...
echo ═══════════════════════════════════════════════════════════════
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python !PYTHON_VERSION! 이미 설치됨
) else (
    echo ❌ Python이 설치되지 않음
    echo.
    echo Python 3.12를 다운로드하고 설치하는 중...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python-installer.exe'"
    echo.
    echo Python 설치를 시작합니다. 
    echo ⚠️  중요: "Add Python to PATH" 체크박스를 반드시 선택하세요!
    start /wait python-installer.exe
    del python-installer.exe
    echo.
    echo Python 설치 완료!
)

echo.
echo [2/7] FFmpeg 설치 중...
echo ═══════════════════════════════════════════════════════════════
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg 이미 설치됨
) else (
    echo FFmpeg 다운로드 중...
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    set "FFMPEG_DIR=C:\ffmpeg"
    
    powershell -Command "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile 'ffmpeg.zip'"
    echo 압축 해제 중...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"
    
    if not exist "!FFMPEG_DIR!" mkdir "!FFMPEG_DIR!"
    for /d %%i in (ffmpeg-*) do (
        xcopy /E /Y "%%i\bin\*" "!FFMPEG_DIR!\bin\" >nul
    )
    
    :: PATH에 FFmpeg 추가
    setx PATH "%PATH%;!FFMPEG_DIR!\bin" >nul
    set "PATH=%PATH%;!FFMPEG_DIR!\bin"
    
    :: 정리
    del ffmpeg.zip
    for /d %%i in (ffmpeg-*) do rmdir /S /Q "%%i"
    
    echo ✅ FFmpeg 설치 완료!
)

echo.
echo [3/7] Python 가상환경 생성 중...
echo ═══════════════════════════════════════════════════════════════
if exist ".venv" (
    echo ⚠️  기존 가상환경 발견. 삭제하고 새로 만들까요? (Y/N)
    set /p REBUILD_VENV=선택: 
    if /i "!REBUILD_VENV!"=="Y" (
        rmdir /S /Q .venv
        python -m venv .venv
        echo ✅ 가상환경 재생성 완료!
    ) else (
        echo ✅ 기존 가상환경 유지
    )
) else (
    python -m venv .venv
    echo ✅ 가상환경 생성 완료!
)

echo.
echo [4/7] GPU (CUDA) 확인 중...
echo ═══════════════════════════════════════════════════════════════
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ NVIDIA GPU 감지됨
    for /f "tokens=2 delims=:" %%i in ('nvidia-smi ^| findstr "CUDA Version"') do (
        set CUDA_VERSION=%%i
        echo    CUDA Version: !CUDA_VERSION!
    )
    set "TORCH_INDEX=https://download.pytorch.org/whl/cu121"
    set "GPU_SUPPORT=1"
) else (
    echo ❌ NVIDIA GPU 없음 (CPU 모드로 설치)
    set "TORCH_INDEX=https://download.pytorch.org/whl/cpu"
    set "GPU_SUPPORT=0"
)

echo.
echo [5/7] Python 패키지 설치 중...
echo ═══════════════════════════════════════════════════════════════
call .venv\Scripts\activate.bat

:: pip 업그레이드
python -m pip install --upgrade pip >nul 2>&1

:: PyTorch 설치
echo    PyTorch 설치 중... (시간이 걸릴 수 있습니다)
if "!GPU_SUPPORT!"=="1" (
    pip install torch torchvision --index-url !TORCH_INDEX!
) else (
    pip install torch torchvision
)

:: 나머지 의존성 설치
echo    기타 패키지 설치 중...
pip install -r requirements.txt

echo ✅ 모든 패키지 설치 완료!

echo.
echo [6/7] 실행 스크립트 생성 중...
echo ═══════════════════════════════════════════════════════════════
:: upscaler.bat 생성 (현재 디렉토리 기반)
echo @echo off > upscaler.bat
echo set "SCRIPT_DIR=%%~dp0" >> upscaler.bat
echo "%%SCRIPT_DIR%%.venv\Scripts\python.exe" -m upscaler %%* >> upscaler.bat

echo ✅ upscaler.bat 생성 완료!

echo.
echo [7/7] 환경변수 설정 중...
echo ═══════════════════════════════════════════════════════════════
:: 현재 사용자 PATH에 추가
for /f "skip=2 tokens=3*" %%a in ('reg query "HKCU\Environment" /v PATH') do set "USER_PATH=%%b"
echo !USER_PATH! | find /i "%PROJECT_DIR%" >nul
if %errorlevel% neq 0 (
    setx PATH "!USER_PATH!;%PROJECT_DIR%" >nul
    echo ✅ PATH에 추가됨: %PROJECT_DIR%
) else (
    echo ✅ 이미 PATH에 포함되어 있음
)

echo.
echo [선택사항] 모델 다운로드
echo ═══════════════════════════════════════════════════════════════
echo AI 모델을 미리 다운로드하시겠습니까? (Y/N)
echo (나중에 첫 실행시 자동으로 다운로드됩니다)
set /p DOWNLOAD_MODELS=선택: 

if /i "!DOWNLOAD_MODELS!"=="Y" (
    echo 모델 다운로드 중...
    call .venv\Scripts\activate.bat
    python -m upscaler models --download realesr-general-x4v3
    python -m upscaler models --download realesrgan-x4plus
    echo ✅ 모델 다운로드 완료!
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                  🎉 설치 완료!                               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 사용 방법:
echo   upscaler image input.jpg output.jpg --scale 4
echo   upscaler video input.mp4 output.mp4 --scale 4
echo.
echo 간편 명령어:
echo   upscaler --help  (도움말 보기)
echo   upscaler doctor  (시스템 진단)
echo.
echo ⚠️  중요: 새 명령 프롬프트를 열어서 사용하세요!
echo.
pause