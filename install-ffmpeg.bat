@echo off
echo ========================================
echo   FFmpeg 다운로드 및 설치 도우미
echo ========================================
echo.

:: FFmpeg 다운로드 URL
set FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
set FFMPEG_DIR=C:\ffmpeg

echo [1] FFmpeg 다운로드 중...
powershell -Command "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile 'ffmpeg.zip'"

echo [2] 압축 해제 중...
powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"

echo [3] FFmpeg 설치 중...
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
xcopy /E /Y "ffmpeg-*\bin\*" "%FFMPEG_DIR%\bin\"

echo [4] PATH 환경변수 추가 중...
setx PATH "%PATH%;%FFMPEG_DIR%\bin"

echo [5] 정리 중...
del ffmpeg.zip
rmdir /S /Q ffmpeg-*

echo.
echo ========================================
echo   FFmpeg 설치 완료!
echo ========================================
echo.
echo 새 명령 프롬프트를 열어서 사용하세요.
echo.
ffmpeg -version
pause
