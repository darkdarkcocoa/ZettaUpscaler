@echo off
echo ========================================
echo   Upscaler 단일 EXE 빌드 (One-File)
echo ========================================
echo.
echo 주의: 단일 파일은 크기가 매우 클 수 있습니다 (2GB+)
echo       첫 실행 시 압축 해제로 시간이 걸립니다
echo.
pause

:: 가상환경 활성화
call D:\Workspace\Upscaler\.venv\Scripts\activate.bat

:: PyInstaller 설치 확인
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    pip install pyinstaller
)

:: 이전 빌드 정리
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

:: 단일 EXE 빌드
echo.
echo 빌드 시작 (10-20분 소요)...
pyinstaller --onefile ^
    --name upscaler ^
    --add-data "upscaler;upscaler" ^
    --hidden-import torch ^
    --hidden-import torchvision ^
    --hidden-import basicsr ^
    --hidden-import realesrgan ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import PIL ^
    --hidden-import tqdm ^
    --hidden-import click ^
    --collect-all torch ^
    --collect-all torchvision ^
    --collect-all basicsr ^
    --collect-all realesrgan ^
    --copy-metadata torch ^
    --copy-metadata torchvision ^
    __main__.py

echo.
echo ========================================
echo   빌드 완료!
echo ========================================
echo.
echo 출력 파일: dist\upscaler.exe
echo 파일 크기: 약 2-3GB
echo.
echo 배포 방법:
echo 1. dist\upscaler.exe 파일만 배포
echo 2. 사용자는 다음과 같이 실행:
echo    upscaler.exe image input.jpg output.jpg --scale 4
echo.
pause
