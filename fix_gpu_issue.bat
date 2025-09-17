@echo off
setlocal enabledelayedexpansion
title ZettaUpscaler GPU 문제 수정 스크립트

echo ================================================================================
echo                     ZettaUpscaler GPU 문제 자동 수정 스크립트
echo ================================================================================
echo.
echo 이 스크립트는 다음 문제를 해결합니다:
echo   - PyTorch CPU 버전이 설치된 경우 GPU 버전으로 재설치
echo   - basicsr/realesrgan 설치 오류 해결
echo   - CUDA 관련 문제 수정
echo.
echo 주의: 가상환경(.venv)가 이미 생성되어 있어야 합니다!
echo.
pause

:: 가상환경 확인
if not exist .venv (
    echo [ERROR] .venv 폴더가 없습니다!
    echo        먼저 install.bat을 실행하세요.
    pause
    exit /b 1
)

:: 가상환경 활성화
echo.
echo [1/6] 가상환경 활성화...
call .venv\Scripts\activate.bat

:: 현재 PyTorch 상태 확인
echo.
echo [2/6] 현재 PyTorch 상태 확인...
python -c "import torch; print(f'PyTorch 버전: {torch.__version__}'); print(f'CUDA 사용 가능: {torch.cuda.is_available()}')" 2>nul
if %errorlevel% neq 0 (
    echo PyTorch가 설치되지 않았습니다.
) else (
    python -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>nul
    if !errorlevel! equ 0 (
        echo.
        echo [OK] PyTorch GPU 버전이 이미 올바르게 설치되어 있습니다!
        set PYTORCH_OK=1
    ) else (
        echo.
        echo [WARNING] PyTorch CPU 버전이 감지되었습니다. GPU 버전으로 재설치합니다.
        set PYTORCH_OK=0
    )
)

:: PyTorch 재설치 필요시
if not defined PYTORCH_OK set PYTORCH_OK=0
if !PYTORCH_OK! equ 0 (
    echo.
    echo [3/6] PyTorch GPU 버전 재설치...
    echo       기존 PyTorch 제거 중...
    pip uninstall torch torchvision torchaudio -y >nul 2>&1

    echo       PyTorch CUDA 12.1 설치 중... (시간이 걸릴 수 있습니다)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir

    if !errorlevel! neq 0 (
        echo.
        echo       CUDA 12.1 실패, CUDA 11.8 시도 중...
        pip install torch==2.2.0+cu118 torchvision==0.17.0+cu118 torchaudio==2.2.0+cu118 --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir

        if !errorlevel! neq 0 (
            echo.
            echo [ERROR] PyTorch GPU 버전 설치 실패!
            echo         네트워크 연결을 확인하세요.
            pause
            exit /b 1
        )
    )

    :: 설치 검증
    echo.
    echo       설치 검증 중...
    python -c "import torch; cuda_ok = torch.cuda.is_available(); print(f'CUDA 사용 가능: {cuda_ok}'); exit(0 if cuda_ok else 1)"
    if !errorlevel! neq 0 (
        echo [ERROR] PyTorch GPU 버전 설치 실패!
        pause
        exit /b 1
    )
    echo [OK] PyTorch GPU 버전 설치 완료!
) else (
    echo [3/6] PyTorch GPU 버전 재설치 건너뛰기 (이미 설치됨)
)

:: numpy 호환성 확인
echo.
echo [4/6] numpy 호환 버전 설치...
pip install numpy==1.26.4 --no-cache-dir >nul 2>&1

:: basicsr/realesrgan 재설치
echo.
echo [5/6] AI 패키지 재설치...

:: basicsr 설치
echo       basicsr 설치 중...
pip uninstall basicsr -y >nul 2>&1
pip install basicsr==1.4.2 --no-cache-dir --no-deps
if !errorlevel! neq 0 (
    echo       [WARNING] basicsr 설치 실패, 의존성과 함께 재시도...
    pip install basicsr==1.4.2 --no-cache-dir
)

:: realesrgan 설치
echo       realesrgan 설치 중...
pip uninstall realesrgan -y >nul 2>&1
pip install realesrgan==0.3.0 --no-cache-dir --no-deps
if !errorlevel! neq 0 (
    echo       [WARNING] realesrgan 설치 실패, 의존성과 함께 재시도...
    pip install realesrgan==0.3.0 --no-cache-dir
)

:: gfpgan, facexlib (선택사항)
echo       추가 패키지 설치 중...
pip install gfpgan>=1.3.8 facexlib>=0.3.0 --no-cache-dir >nul 2>&1

:: 나머지 requirements 설치
echo       나머지 패키지 설치 중...
pip install -r requirements.txt >nul 2>&1

:: 최종 검증
echo.
echo [6/6] 최종 검증...
echo.

python -c "import torch; print(f'✅ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')"
python -c "import basicsr; print('✅ basicsr 설치됨')" 2>nul || echo ❌ basicsr 설치 실패
python -c "import realesrgan; print('✅ realesrgan 설치됨')" 2>nul || echo ❌ realesrgan 설치 실패
python -c "from realesrgan import RealESRGANer; print('✅ RealESRGANer import 성공')" 2>nul || echo ❌ RealESRGANer import 실패

:: 백엔드 테스트
echo.
echo 백엔드 자동 선택 테스트...
python -c "import sys; sys.path.insert(0, '.'); from upscaler.backends import get_backend; b = get_backend('auto'); print(f'✅ 선택된 백엔드: {b.__class__.__name__}')" 2>nul
if !errorlevel! neq 0 (
    echo ❌ 백엔드 선택 실패
)

:: 빠른 테스트
echo.
echo ================================================================================
echo                               수정 완료!
echo ================================================================================
echo.
echo 이제 다음 명령으로 테스트해보세요:
echo   python -m upscaler doctor
echo   python -m upscaler image 1.png output.png --scale 4
echo.
echo 문제가 계속되면 diagnose_gpu_issue.py를 실행하여 로그를 공유해주세요.
echo.
pause