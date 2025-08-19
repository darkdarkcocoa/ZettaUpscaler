@echo off
echo ========================================
echo   시스템 Python 정리 스크립트
echo ========================================
echo.
echo 이 스크립트는 시스템 Python에서 
echo AI 업스케일링 관련 패키지를 제거합니다.
echo.
echo 제거할 패키지:
echo - torch, torchvision (CPU 버전)
echo - basicsr, realesrgan, gfpgan
echo - 관련 의존성들
echo.
pause

echo.
echo [1/3] PyTorch 관련 제거 중...
pip uninstall torch torchvision torchaudio -y

echo.
echo [2/3] AI 업스케일링 패키지 제거 중...
pip uninstall basicsr realesrgan gfpgan facexlib -y

echo.
echo [3/3] 캐시 정리 중...
pip cache purge

echo.
echo ========================================
echo   정리 완료!
echo ========================================
echo.
echo 이제 가상환경만 사용하세요:
echo   cd D:\Workspace\Upscaler
echo   .\.venv\Scripts\activate
echo.
echo 또는 배치 파일 사용:
echo   upscaler-gpu image input.jpg output.jpg
echo.
pause
