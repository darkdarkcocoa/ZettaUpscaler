@echo off
echo ========================================
echo   GitHub 푸시 (인증 필요)
echo ========================================
echo.
echo GitHub에 푸시하려면 다음 중 하나가 필요합니다:
echo.
echo 1. GitHub Desktop 사용 (가장 쉬움)
echo    - GitHub Desktop 설치
echo    - File → Add Local Repository
echo    - D:\Workspace\Upscaler 선택
echo    - Publish Repository 클릭
echo.
echo 2. Personal Access Token 사용
echo    - https://github.com/settings/tokens 접속
echo    - Generate new token (classic) 클릭
echo    - repo 권한 체크
echo    - 생성된 토큰 복사
echo.
echo 3. Git Credential Manager 사용 (자동)
echo    - 아래 명령 실행 시 GitHub 로그인 창 표시
echo.
echo 준비되셨으면 Enter를 누르세요...
pause >nul
echo.

:: 푸시 시도
echo GitHub에 푸시 중...
git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo   성공적으로 업로드되었습니다!
    echo ========================================
    echo.
    echo 저장소 확인: https://github.com/darkdarkcocoa/ZettaUpscaler
    echo.
) else (
    echo ========================================
    echo   푸시 실패 - 인증 문제
    echo ========================================
    echo.
    echo 해결 방법:
    echo 1. Personal Access Token 생성하기
    echo    https://github.com/settings/tokens
    echo.
    echo 2. 다음 명령 실행:
    echo    git remote set-url origin https://TOKEN@github.com/darkdarkcocoa/ZettaUpscaler.git
    echo    (TOKEN을 실제 토큰으로 교체)
    echo.
    echo 3. 다시 푸시:
    echo    git push -u origin main
    echo.
)

pause