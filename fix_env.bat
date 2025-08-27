@echo off
echo ========================================
echo Fixing ZettaUpscaler Environment
echo ========================================
echo.

cd /d "%~dp0"

echo [1] Checking Python versions...
echo Local Python:
python --version 2>nul
where python

echo.
echo Virtual env Python:
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" --version
    echo Path: %~dp0.venv\Scripts\python.exe
) else (
    echo ERROR: Virtual environment not found!
    echo Creating new virtual environment with Python 3.12...
    
    :: Try to use Python 3.12 specifically
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        py -3.12 -m venv .venv
    ) else (
        python -m venv .venv
    )
)

echo.
echo [2] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [3] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [4] Cleaning old packages...
pip cache purge

echo.
echo [5] Installing PyTorch for NVIDIA GPU (CUDA 12.1)...
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo [6] Installing other requirements...
pip install -r requirements.txt --force-reinstall

echo.
echo [7] Verifying installation...
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')"

echo.
echo [8] Testing upscaler import...
python -c "from upscaler import __version__; print(f'Upscaler OK')"

echo.
echo ========================================
echo Fix complete! 
echo.
echo Test with: upscaler.bat --help
echo ========================================
pause