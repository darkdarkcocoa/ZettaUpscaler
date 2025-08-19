@echo off
echo ========================================
echo   ZettaUpscaler Git 초기화 및 업로드
echo ========================================
echo.

:: Git 초기화
echo [1/7] Git 저장소 초기화 중...
git init

:: Git 사용자 설정 (필요시 수정하세요)
echo [2/7] Git 사용자 설정 중...
git config user.name "darkdarkcocoa"
git config user.email "your-email@example.com"

:: 원격 저장소 추가
echo [3/7] GitHub 원격 저장소 연결 중...
git remote add origin https://github.com/darkdarkcocoa/ZettaUpscaler.git

:: 모든 파일 추가
echo [4/7] 파일 추가 중...
git add .

:: 첫 커밋
echo [5/7] 첫 커밋 생성 중...
git commit -m "Initial commit: ZettaUpscaler - AI-powered video/image upscaling tool"

:: 브랜치 이름 설정 (main)
echo [6/7] 브랜치 설정 중...
git branch -M main

:: GitHub에 푸시
echo [7/7] GitHub에 업로드 중...
echo.
echo GitHub 인증이 필요합니다.
echo 옵션 1: GitHub 웹사이트에서 로그인 창이 열립니다
echo 옵션 2: Personal Access Token을 입력하세요
echo.
git push -u origin main

echo.
echo ========================================
echo   업로드 완료!
echo ========================================
echo.
echo 저장소 URL: https://github.com/darkdarkcocoa/ZettaUpscaler
echo.
echo 다음 단계:
echo 1. GitHub에서 저장소 확인
echo 2. README.md 미리보기 확인
echo 3. Releases 탭에서 배포 파일 업로드
echo.
pause