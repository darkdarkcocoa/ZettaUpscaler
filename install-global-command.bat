@echo off
echo ========================================
echo   Upscaler 전역 설치
echo ========================================
echo.

:: 가상환경 활성화
call D:\Workspace\Upscaler\.venv\Scripts\activate.bat

:: pip로 editable 설치 (개발 모드)
cd D:\Workspace\Upscaler
pip install -e .

:: Scripts 폴더를 PATH에 추가
set SCRIPTS_PATH=D:\Workspace\Upscaler\.venv\Scripts
setx PATH "%PATH%;%SCRIPTS_PATH%"

echo.
echo ========================================
echo   설치 완료!
echo ========================================
echo.
echo 이제 새 터미널에서 사용 가능:
echo   upscaler image input.jpg output.jpg
echo   upscaler video input.mp4 output.mp4
echo.
echo (터미널을 재시작해야 PATH가 적용됩니다)
echo.
pause
