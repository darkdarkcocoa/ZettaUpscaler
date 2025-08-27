@echo off
echo ========================================
echo   Upscaler EXE 빌드 스크립트
echo ========================================
echo.

:: 가상환경 활성화
echo [1/5] 가상환경 활성화 중...
call D:\Workspace\Upscaler\.venv\Scripts\activate.bat

:: PyInstaller 설치 확인
echo.
echo [2/5] PyInstaller 설치 확인 중...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller 설치 중...
    pip install pyinstaller
) else (
    echo PyInstaller 이미 설치됨
)

:: 이전 빌드 정리
echo.
echo [3/5] 이전 빌드 정리 중...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

:: EXE 빌드 (폴더 형태)
echo.
echo [4/5] EXE 빌드 시작 (폴더 형태)...
echo 이 작업은 몇 분 걸릴 수 있습니다...
pyinstaller --clean upscaler.spec

:: 모델 파일 복사
echo.
echo [5/5] 모델 파일 복사 중...
if not exist "dist\upscaler\models" mkdir "dist\upscaler\models"
xcopy /E /I /Y ".venv\Lib\site-packages\basicsr\archs" "dist\upscaler\basicsr\archs"
xcopy /E /I /Y ".venv\Lib\site-packages\realesrgan\weights" "dist\upscaler\models" 2>nul

:: 배치 파일 생성
echo @echo off > "dist\upscaler\upscaler.bat"
echo upscaler.exe %%* >> "dist\upscaler\upscaler.bat"

echo.
echo ========================================
echo   빌드 완료!
echo ========================================
echo.
echo 출력 위치: dist\upscaler\
echo 실행 파일: dist\upscaler\upscaler.exe
echo.
echo 사용 방법:
echo   cd dist\upscaler
echo   upscaler.exe image input.jpg output.jpg --scale 4
echo.
pause
