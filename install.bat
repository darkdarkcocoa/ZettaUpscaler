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
:: Python 3.12 우선 확인
set "PYTHON_FOUND=0"
set "PYTHON_VERSION="

:: py launcher로 3.12 확인
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3.12 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%i in ('py -3.12 --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo ✅ Python 3.12 발견! (py -3.12)
        set "PYTHON_FOUND=1"
    )
)

:: 기본 Python 확인
if "!PYTHON_FOUND!"=="0" (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
        echo ⚠️  Python !PYTHON_VERSION! 발견
        echo    프로젝트는 Python 3.12 권장! (현재: !PYTHON_VERSION!)
        set "PYTHON_FOUND=1"
    )
)

if "!PYTHON_FOUND!"=="0" (
    echo ❌ Python이 설치되지 않음
    echo.
    echo Python 3.12를 다운로드하고 설치하는 중...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python-installer.exe'"
    echo.
    echo Python 설치를 시작합니다. 
    echo ⚠️  중요: ComfyUI와 충돌 피하려면 "Add Python to PATH" 체크 해제!
    echo    대신 py launcher 사용을 권장합니다.
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
    
    :: 현재 세션에만 PATH 추가 (안전)
    set "PATH=%PATH%;!FFMPEG_DIR!\bin"
    
    :: 영구 PATH 추가를 위한 안내
    echo.
    echo ⚠️  FFmpeg을 영구적으로 사용하려면:
    echo    1. Windows 설정 → 시스템 → 정보 → 고급 시스템 설정
    echo    2. 환경 변수 → Path 편집
    echo    3. "!FFMPEG_DIR!\bin" 추가
    echo.
    
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
        :: Python 3.12 있으면 그걸로, 없으면 기본 Python으로
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv || python -m venv .venv
    ) else (
        python -m venv .venv
    )
        echo ✅ 가상환경 재생성 완료!
    ) else (
        echo ✅ 기존 가상환경 유지
    )
) else (
    :: Python 3.12 있으면 그걸로, 없으면 기본 Python으로
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3.12 -m venv .venv 2>nul || py -3 -m venv .venv || python -m venv .venv
    ) else (
        python -m venv .venv
    )
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
    echo    [GPU 버전 설치중...]
    pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
) else (
    echo    [CPU 버전 설치중...]
    pip install torch torchvision
)

:: 나머지 의존성 설치
echo    기타 패키지 설치 중...
pip install -r requirements.txt

echo ✅ 모든 패키지 설치 완료!

echo.
echo [6/7] 실행 스크립트 확인 중...
echo ═══════════════════════════════════════════════════════════════
:: upscaler.bat이 이미 있는지 확인
if exist upscaler.bat (
    echo ✅ upscaler.bat 이미 존재함
) else (
    :: upscaler.bat 생성 (현재 디렉토리 기반)
    (
        echo @echo off
        echo setlocal
        echo set "SCRIPT_DIR=%%~dp0"
        echo cd /d "%%SCRIPT_DIR%%"
        echo.
        echo :: 가상환경 Python 경로를 정확히 지정 ^(따옴표 중요!^)
        echo set "PYTHON_EXE=%%SCRIPT_DIR%%.venv\Scripts\python.exe"
        echo.
        echo :: 가상환경 Python이 있는지 확인
        echo if not exist "%%PYTHON_EXE%%" ^(
        echo     echo Error: Virtual environment not found!
        echo     echo Please run install.bat first
        echo     pause
        echo     exit /b 1
        echo ^)
        echo.
        echo :: upscaler 실행
        echo "%%PYTHON_EXE%%" -m upscaler %%*
    ) > upscaler.bat
    echo ✅ upscaler.bat 생성 완료!
)

echo.
echo [7/7] 환경변수 설정 중...
echo ═══════════════════════════════════════════════════════════════
:: PATH 추가 헬퍼 파일 생성
echo @echo off > add-to-path.bat
echo :: ZettaUpscaler PATH 추가 스크립트 >> add-to-path.bat
echo set "PATH=%%PATH%%;%PROJECT_DIR%" >> add-to-path.bat
echo echo ZettaUpscaler가 현재 세션의 PATH에 추가되었습니다. >> add-to-path.bat
echo echo upscaler 명령을 사용할 수 있습니다! >> add-to-path.bat

echo ✅ add-to-path.bat 생성 완료!
echo.
echo 💡 팁: 새 명령 프롬프트를 열 때마다 'add-to-path.bat'를 실행하면
echo    어디서든 'upscaler' 명령을 사용할 수 있습니다.
echo.
echo 📌 영구 설정을 원하시면:
echo    1. Windows 설정 → 시스템 → 정보 → 고급 시스템 설정
echo    2. 환경 변수 → Path 편집
echo    3. "%PROJECT_DIR%" 추가

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
echo 🚀 사용 방법:
echo.
echo 방법 1) 현재 폴더에서 직접 실행:
echo   .\upscaler image input.jpg output.jpg --scale 4
echo   .\upscaler video input.mp4 output.mp4 --scale 4
echo.
echo 방법 2) 어디서든 사용하기 (권장):
echo   1. 새 명령 프롬프트 열기
echo   2. add-to-path.bat 실행
echo   3. upscaler 명령 사용
echo.
echo 간편 명령어:
echo   upscaler --help  (도움말 보기)
echo   upscaler doctor  (시스템 진단)
echo.
echo 💡 참고: 환경변수 안전을 위해 setx를 사용하지 않습니다.
echo         add-to-path.bat를 사용하면 안전하게 PATH에 추가됩니다.
echo.
pause