@echo off
echo ========================================
echo   시스템 Python GPU 설정 스크립트
echo ========================================
echo.
echo RTX 4060 Ti용 CUDA 12.1 버전으로
echo 시스템 Python을 설정합니다.
echo.
pause

echo.
echo [1/5] 기존 CPU 버전 제거 중...
pip uninstall torch torchvision torchaudio -y

echo.
echo [2/5] GPU 버전 PyTorch 설치 중 (약 2.5GB)...
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 --index-url https://download.pytorch.org/whl/cu121

echo.
echo [3/5] NumPy 버전 조정 중...
pip uninstall numpy -y
pip install numpy==1.26.4

echo.
echo [4/5] AI 업스케일링 패키지 재설치 중...
pip uninstall basicsr realesrgan gfpgan -y
pip install basicsr==1.4.2 realesrgan==0.3.0 gfpgan==1.3.8

echo.
echo [5/5] 호환성 문제 수정 중...
python D:\Workspace\Upscaler\fix_compatibility.py

echo.
echo ========================================
echo   GPU 테스트
echo ========================================
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"Not Available\"}')"

echo.
echo ========================================
echo   설치 완료!
echo ========================================
echo.
echo 이제 어디서나 사용 가능:
echo   python -m upscaler image input.jpg output.jpg --scale 4
echo.
echo 또는 pip install로 전역 설치:
echo   cd D:\Workspace\Upscaler
echo   pip install -e .
echo.
pause
