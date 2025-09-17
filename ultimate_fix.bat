@echo off
setlocal enabledelayedexpansion
title ZettaUpscaler - 최종 완벽 수정 스크립트

cls
echo ================================================================================
echo                    ZettaUpscaler 최종 완벽 수정 스크립트
echo ================================================================================
echo.
echo 이 스크립트는 모든 문제를 해결합니다:
echo   1. torchvision 호환성 문제
echo   2. CUDA 인식 문제
echo   3. basicsr/realesrgan import 오류
echo.
echo 시작하려면 아무 키나 누르세요...
pause >nul

:: 가상환경 확인
if not exist .venv (
    echo.
    echo [ERROR] .venv가 없습니다! install.bat을 먼저 실행하세요.
    pause
    exit /b 1
)

:: 가상환경 활성화
echo.
echo [1/5] 가상환경 활성화...
call .venv\Scripts\activate.bat

:: 기존 패키지 완전 제거
echo.
echo [2/5] 기존 패키지 완전 제거...
pip uninstall torch torchvision torchaudio basicsr realesrgan gfpgan -y >nul 2>&1

:: PyTorch + torchvision 호환 버전 설치
echo.
echo [3/5] PyTorch와 호환되는 torchvision 설치...
echo       이 작업은 시간이 걸릴 수 있습니다...

:: PyTorch 2.1.0 + torchvision 0.16.0 조합 (basicsr과 호환)
pip install torch==2.1.0+cu118 torchvision==0.16.0+cu118 torchaudio==2.1.0+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir

if %errorlevel% neq 0 (
    echo.
    echo   첫 번째 시도 실패, 대체 버전 시도...
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir
)

:: numpy 호환 버전 확인
pip install numpy==1.26.4 --no-cache-dir >nul 2>&1

:: AI 패키지 설치
echo.
echo [4/5] AI 패키지 설치...

:: basicsr 설치
echo       - basicsr 설치 중...
pip install basicsr==1.4.2 --no-cache-dir --no-deps
pip install -r requirements.txt --no-cache-dir >nul 2>&1

:: realesrgan 설치
echo       - realesrgan 설치 중...
pip install realesrgan==0.3.0 --no-cache-dir

:: gfpgan/facexlib 설치
echo       - 추가 패키지 설치 중...
pip install gfpgan>=1.3.8 facexlib>=0.3.0 --no-cache-dir >nul 2>&1

:: 패치 적용 (필요시)
echo.
echo [5/5] 호환성 패치 적용...
python patch_basicsr.py >nul 2>&1

:: 최종 검증
echo.
echo ================================================================================
echo                               최종 검증
echo ================================================================================
echo.

:: Python 버전
python -c "import sys; print(f'Python: {sys.version.split()[0]}')"

:: PyTorch 검증
python -c "import torch; print(f'PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})')"
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')"

:: basicsr/realesrgan 검증
echo.
python -c "import basicsr; print('✅ basicsr import 성공')" 2>nul || echo ❌ basicsr import 실패
python -c "import realesrgan; print('✅ realesrgan import 성공')" 2>nul || echo ❌ realesrgan import 실패
python -c "from realesrgan import RealESRGANer; print('✅ RealESRGANer import 성공')" 2>nul || echo ❌ RealESRGANer import 실패

:: 백엔드 테스트
echo.
echo 백엔드 선택 테스트...
python -c "import sys; sys.path.insert(0, '.'); from upscaler.backends import get_backend; b = get_backend('auto'); print(f'✅ 활성화된 백엔드: {b.__class__.__name__}')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 백엔드 선택 실패
)

:: GPU 메모리 체크
echo.
python -c "import torch; print(f'GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB') if torch.cuda.is_available() else print('GPU 사용 불가')" 2>nul

echo.
echo ================================================================================
echo                          수정 완료!
echo ================================================================================
echo.
echo 이제 테스트해보세요:
echo.
echo   1. 시스템 체크:
echo      python -m upscaler doctor
echo.
echo   2. 이미지 업스케일:
echo      python -m upscaler image 1.png output.png --scale 4
echo.
echo   3. 비디오 업스케일:
echo      python -m upscaler video input.mp4 output.mp4 --scale 4
echo.
echo 문제가 계속되면 diagnose_gpu_issue_venv.bat 결과를 공유해주세요.
echo ================================================================================
pause