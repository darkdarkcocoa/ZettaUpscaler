@echo off
setlocal enabledelayedexpansion
title ZettaUpscaler - Torchvision 호환성 문제 수정

echo ================================================================================
echo              Torchvision 호환성 문제 자동 수정 스크립트
echo ================================================================================
echo.
echo 문제: torchvision.transforms.functional_tensor 모듈을 찾을 수 없음
echo 원인: torchvision 버전과 basicsr 비호환
echo.
pause

:: 가상환경 활성화
if not exist .venv (
    echo [ERROR] .venv 폴더가 없습니다!
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo.
echo [방법 1] torchvision 다운그레이드 (권장)
echo ================================================================================
echo.
echo 현재 버전 제거 중...
pip uninstall torchvision -y

echo.
echo torchvision 0.15.2 설치 중 (basicsr과 호환)...
pip install torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir

if %errorlevel% neq 0 (
    echo.
    echo [방법 2] 대체 버전 시도
    echo ================================================================================
    pip install torchvision==0.16.0+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir
)

echo.
echo basicsr 재설치 중...
pip uninstall basicsr -y
pip install basicsr==1.4.2 --no-cache-dir

echo.
echo realesrgan 재설치 중...
pip uninstall realesrgan -y
pip install realesrgan==0.3.0 --no-cache-dir

echo.
echo ================================================================================
echo                            검증 중...
echo ================================================================================
echo.

:: 테스트
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')"
python -c "import basicsr; print('basicsr: OK')" 2>nul
if %errorlevel% neq 0 (
    echo basicsr: FAILED
) else (
    echo basicsr: OK
)

python -c "import realesrgan; print('realesrgan: OK')" 2>nul
if %errorlevel% neq 0 (
    echo realesrgan: FAILED
) else (
    echo realesrgan: OK
)

echo.
echo 백엔드 테스트...
python -c "import sys; sys.path.insert(0, '.'); from upscaler.backends import get_backend; b = get_backend('auto'); print(f'선택된 백엔드: {b.__class__.__name__}')" 2>nul

echo.
echo ================================================================================
echo 수정 완료! 이제 다시 테스트해보세요:
echo   python -m upscaler doctor
echo   python -m upscaler image 1.png output.png --scale 4
echo ================================================================================
pause