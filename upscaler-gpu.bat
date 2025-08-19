@echo off
:: Upscaler 실행 배치 파일
:: 가상환경의 Python과 upscaler를 직접 실행

set VENV_PATH=D:\Workspace\Upscaler\.venv
set PYTHON=%VENV_PATH%\Scripts\python.exe

:: 인자가 없으면 도움말 표시
if "%~1"=="" (
    echo.
    echo ========================================
    echo   AI Video/Image Upscaler
    echo ========================================
    echo.
    echo Usage:
    echo   upscaler-gpu image input.jpg output.jpg [options]
    echo   upscaler-gpu video input.mp4 output.mp4 [options]
    echo.
    echo Options:
    echo   --scale 2/4     : Upscale factor (default: 4)
    echo   --model NAME    : Model name
    echo   --copy-audio    : Copy audio for video
    echo.
    echo Examples:
    echo   upscaler-gpu image photo.jpg photo_4x.jpg --scale 4
    echo   upscaler-gpu video movie.mp4 movie_4x.mp4 --copy-audio
    echo.
    %PYTHON% -m upscaler --help
) else (
    :: upscaler 실행
    %PYTHON% -m upscaler %*
)
