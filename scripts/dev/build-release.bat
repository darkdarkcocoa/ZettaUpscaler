@echo off
echo ========================================
echo   Upscaler 릴리즈 빌드 v1.0.0
echo ========================================
echo.

:: 버전 정보
set VERSION=1.0.0
set RELEASE_NAME=upscaler-%VERSION%-win64

:: 프로젝트 루트로 이동
cd /d %~dp0\..\..

:: 가상환경 활성화
call .venv\Scripts\activate.bat

:: PyInstaller 설치
pip install pyinstaller >nul 2>&1

:: 클린 빌드
echo [1/5] 이전 빌드 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "releases" mkdir releases

echo [2/5] EXE 빌드 중 (5-10분 소요)...
pyinstaller --noconfirm ^
    --name upscaler ^
    --console ^
    --add-data "upscaler;upscaler" ^
    --hidden-import torch ^
    --hidden-import torchvision ^
    --hidden-import basicsr ^
    --hidden-import realesrgan ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import colorama ^
    --hidden-import humanize ^
    --collect-all torch ^
    --collect-all torchvision ^
    __main__.py

echo [3/5] 릴리즈 폴더 준비 중...
mkdir "releases\%RELEASE_NAME%"
xcopy /E /I /Y "dist\upscaler" "releases\%RELEASE_NAME%\"

echo [4/5] 문서 추가 중...
:: README 생성
echo AI Video/Image Upscaler v%VERSION% > "releases\%RELEASE_NAME%\README.txt"
echo ======================================== >> "releases\%RELEASE_NAME%\README.txt"
echo. >> "releases\%RELEASE_NAME%\README.txt"
echo 사용법: >> "releases\%RELEASE_NAME%\README.txt"
echo   upscaler.exe image input.jpg output.jpg --scale 4 >> "releases\%RELEASE_NAME%\README.txt"
echo   upscaler.exe video input.mp4 output.mp4 --scale 4 --copy-audio >> "releases\%RELEASE_NAME%\README.txt"
echo. >> "releases\%RELEASE_NAME%\README.txt"
echo GPU: NVIDIA GPU가 있으면 자동으로 사용됩니다. >> "releases\%RELEASE_NAME%\README.txt"
echo 모델: 첫 실행 시 자동으로 다운로드됩니다. >> "releases\%RELEASE_NAME%\README.txt"

:: 배치 파일 생성
echo @echo off > "releases\%RELEASE_NAME%\upscale-image.bat"
echo upscaler.exe image %%1 "%%~n1_4x%%~x1" --scale 4 >> "releases\%RELEASE_NAME%\upscale-image.bat"

echo [5/5] ZIP 압축 중...
powershell -Command "Compress-Archive -Path 'releases\%RELEASE_NAME%' -DestinationPath 'releases\%RELEASE_NAME%.zip' -Force"

:: 파일 크기 확인
for %%A in ("releases\%RELEASE_NAME%.zip") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE%/1048576

echo.
echo ========================================
echo   빌드 완료!
echo ========================================
echo.
echo 릴리즈 파일: releases\%RELEASE_NAME%.zip
echo 파일 크기: 약 %SIZE_MB% MB
echo.
echo 배포 방법:
echo 1. releases\%RELEASE_NAME%.zip 파일 업로드
echo 2. 사용자는 압축 해제 후 upscaler.exe 실행
echo.
pause
