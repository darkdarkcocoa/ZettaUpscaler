# ZettaUpscaler PowerShell Installer
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

# 색상 함수
function Write-Title {
    param([string]$Text)
    Write-Host "`n$Text" -ForegroundColor Cyan -BackgroundColor Black
    Write-Host ("=" * $Text.Length) -ForegroundColor DarkCyan
}

function Write-Step {
    param([string]$Text)
    Write-Host "`n[$Text]" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "  ✓ $Text" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Text)
    Write-Host "  ! $Text" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "  ✗ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "  → $Text" -ForegroundColor Gray
}

# 관리자 권한 체크
function Test-Admin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 메인 설치 시작
Clear-Host
$Host.UI.RawUI.WindowTitle = "ZettaUpscaler Installer (PowerShell)"

Write-Host @"

    ╔══════════════════════════════════════════════════════════╗
    ║              🚀 ZettaUpscaler Installer                  ║
    ║                    Version 1.0                           ║
    ╚══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "  Real-ESRGAN 기반 AI 이미지/영상 업스케일링 도구" -ForegroundColor White
Write-Host "  NVIDIA GPU 가속으로 최대 4배 해상도 향상`n" -ForegroundColor Gray

Write-Host "  설치될 항목:" -ForegroundColor White
Write-Host "    • Python 3.12 (필요시)" -ForegroundColor Gray
Write-Host "    • FFmpeg (영상 처리용)" -ForegroundColor Gray  
Write-Host "    • Python 가상환경" -ForegroundColor Gray
At Write-Host "    • 필수 패키지 (PyTorch, Real-ESRGAN 등)" -ForegroundColor Gray
Write-Host "    • 안전한 환경변수 설정`n" -ForegroundColor Gray

# 관리자 권한 확인
if (-not (Test-Admin)) {
    Write-Error "관리자 권한이 필요합니다!"
    Write-Host "`n  다음과 같이 실행해주세요:" -ForegroundColor Yellow
    Write-Host "  1. PowerShell을 관리자로 실행" -ForegroundColor White
    Write-Host "  2. 다음 명령 입력:" -ForegroundColor White
    Write-Host "     cd '$PSScriptRoot'" -ForegroundColor Green
    Write-Host "     powershell -ExecutionPolicy Bypass -File install.ps1`n" -ForegroundColor Green
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "계속하려면 Enter를 누르세요..." -ForegroundColor DarkGray
Read-Host

# 프로젝트 디렉토리 설정
$ProjectDir = $PSScriptRoot
Set-Location $ProjectDir

# Step 1: Python 확인
Write-Step "Step 1/7: Python 설치 확인"

$Python312Found = $false
$PythonVersion = ""

# py launcher로 3.12 확인
try {
    $pyVersion = & py -3.12 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $PythonVersion = ($pyVersion -split ' ')[1]
        Write-Success "Python 3.12 발견! (py launcher 사용)"
        $Python312Found = $true
    }
} catch {}

# 기본 Python 확인
if (-not $Python312Found) {
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            $PythonVersion = ($pythonVersion -split ' ')[1]
            Write-Warning "Python $PythonVersion 발견"
            Write-Info "권장: Python 3.12 (현재: $PythonVersion)"
        }
    } catch {
        Write-Error "Python이 설치되지 않음"
        Write-Info "Python 3.12를 다운로드하고 설치합니다..."
        
        $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
        $pythonInstaller = "$env:TEMP\python-installer.exe"
        
        Write-Info "다운로드 중..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
        
        Write-Warning "Python 설치시 주의사항:"
        Write-Info "- 'Add Python to PATH' 체크 해제 (ComfyUI 충돌 방지)"
        Write-Info "- py launcher는 설치"
        
        Start-Process -FilePath $pythonInstaller -Wait
        Remove-Item $pythonInstaller
        
        Write-Success "Python 설치 완료"
    }
}

# Step 2: FFmpeg 설치
Write-Step "Step 2/7: FFmpeg 설치"

$ffmpegPath = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegPath) {
    Write-Success "FFmpeg 이미 설치됨"
} else {
    Write-Info "FFmpeg 다운로드 중..."
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $ffmpegZip = "$env:TEMP\ffmpeg.zip"
    $ffmpegDir = "C:\ffmpeg"
    
    # 프로그레스 바와 함께 다운로드
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($ffmpegUrl, $ffmpegZip)
    
    Write-Info "압축 해제 중..."
    Expand-Archive -Path $ffmpegZip -DestinationPath $env:TEMP -Force
    
    if (-not (Test-Path $ffmpegDir)) {
        New-Item -ItemType Directory -Path $ffmpegDir | Out-Null
    }
    
    $ffmpegExtracted = Get-ChildItem -Path $env:TEMP -Filter "ffmpeg-*" -Directory | Select-Object -First 1
    Copy-Item -Path "$($ffmpegExtracted.FullName)\bin\*" -Destination "$ffmpegDir\bin" -Force -Recurse
    
    # 현재 세션 PATH 추가
    $env:Path += ";$ffmpegDir\bin"
    
    # 정리
    Remove-Item $ffmpegZip
    Remove-Item $ffmpegExtracted.FullName -Recurse -Force
    
    Write-Success "FFmpeg 설치 완료"
    Write-Info "영구 사용을 위해 시스템 환경변수에 추가 필요"
}

# Step 3: 가상환경 생성
Write-Step "Step 3/7: Python 가상환경 생성"

if (Test-Path ".venv") {
    Write-Warning "기존 가상환경 발견"
    $rebuild = Read-Host "  재생성하시겠습니까? (Y/N)"
    
    if ($rebuild -eq 'Y') {
        Write-Info "기존 환경 삭제 중..."
        Remove-Item -Path .venv -Recurse -Force
        
        Write-Info "새 가상환경 생성 중..."
        if (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3.12 -m venv .venv 2>$null || & py -3 -m venv .venv || & python -m venv .venv
        } else {
            & python -m venv .venv
        }
        Write-Success "가상환경 재생성 완료"
    } else {
        Write-Success "기존 가상환경 유지"
    }
} else {
    Write-Info "가상환경 생성 중..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv .venv 2>$null || & py -3 -m venv .venv || & python -m venv .venv
    } else {
        & python -m venv .venv
    }
    Write-Success "가상환경 생성 완료"
}

# Step 4: GPU 확인
Write-Step "Step 4/7: GPU 지원 확인"

$gpuSupport = $false
try {
    $nvidiaInfo = & nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "NVIDIA GPU 감지됨"
        
        # CUDA 버전 추출
        $cudaLine = $nvidiaInfo | Select-String "CUDA Version"
        if ($cudaLine) {
            $cudaVersion = ($cudaLine -split ":")[1].Trim()
            Write-Info "CUDA Version: $cudaVersion"
        }
        
        $torchIndex = "https://download.pytorch.org/whl/cu121"
        $gpuSupport = $true
    }
} catch {}

if (-not $gpuSupport) {
    Write-Warning "NVIDIA GPU 없음 (CPU 모드로 설치)"
    $torchIndex = "https://download.pytorch.org/whl/cpu"
}

# Step 5: 패키지 설치
Write-Step "Step 5/7: Python 패키지 설치"

Write-Info "가상환경 활성화 중..."
& ".\.venv\Scripts\Activate.ps1"

Write-Info "pip 업그레이드 중..."
& python -m pip install --upgrade pip | Out-Null

Write-Info "PyTorch 설치 중... (시간이 걸릴 수 있습니다)"
if ($gpuSupport) {
    Write-Host "  [GPU 버전 - NVIDIA 카드에 최적화]" -ForegroundColor Green
    & pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url $torchIndex
} else {
    Write-Host "  [CPU 버전 - GPU 가속 없음]" -ForegroundColor Yellow
    & pip install torch torchvision
}

Write-Info "기타 패키지 설치 중..."
& pip install -r requirements.txt

Write-Success "모든 패키지 설치 완료"

# Step 6: 실행 스크립트 생성
Write-Step "Step 6/7: 실행 스크립트 생성"

if (Test-Path "upscaler.bat") {
    Write-Success "upscaler.bat 이미 존재"
} else {
    $upscalerContent = @'
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Use virtual environment Python
set "PYTHON_EXE=%SCRIPT_DIR%.venv\Scripts\python.exe"

:: Check if virtual environment exists
if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found!
    echo Please run install.bat first
    pause
    exit /b 1
)

:: Run upscaler
"%PYTHON_EXE%" -m upscaler %*
'@
    
    Set-Content -Path "upscaler.bat" -Value $upscalerContent
    Write-Success "upscaler.bat 생성 완료"
}

# PowerShell 버전도 생성
$upscalerPs1Content = @'
# ZettaUpscaler PowerShell Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run install.ps1 first" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

& $pythonExe -m upscaler $args
'@

Set-Content -Path "upscaler.ps1" -Value $upscalerPs1Content
Write-Success "upscaler.ps1 생성 완료"

# Step 7: PATH 헬퍼 생성
Write-Step "Step 7/7: PATH 헬퍼 설정"

$pathHelperContent = @"
@echo off
:: ZettaUpscaler PATH helper
set "PATH=%PATH%;$ProjectDir"
echo ZettaUpscaler has been added to PATH for this session.
echo You can now use 'upscaler' from anywhere!
"@

Set-Content -Path "add-to-path.bat" -Value $pathHelperContent
Write-Success "add-to-path.bat 생성 완료"

# 선택: 모델 다운로드
Write-Host "`n" -NoNewline
Write-Title "선택사항: AI 모델 다운로드"

Write-Host "`n  AI 모델은 첫 사용시 자동 다운로드됩니다." -ForegroundColor Gray
Write-Host "  지금 미리 다운로드할 수도 있습니다. (권장)`n" -ForegroundColor Gray

$downloadModels = Read-Host "  모델을 지금 다운로드하시겠습니까? (Y/N)"

if ($downloadModels -eq 'Y') {
    Write-Info "모델 다운로드 중..."
    & python -m upscaler models --download realesr-general-x4v3
    & python -m upscaler models --download realesrgan-x4plus
    Write-Success "모델 다운로드 완료"
}

# 설치 완료
Clear-Host
Write-Host @"

    ╔══════════════════════════════════════════════════════════╗
    ║              ✅ 설치가 완료되었습니다!                   ║
    ╚══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Title "사용 방법"

Write-Host "`n  방법 1 - 현재 폴더에서:" -ForegroundColor Yellow
Write-Host "    .\upscaler image input.jpg output.jpg --scale 4" -ForegroundColor White
Write-Host "    .\upscaler video input.mp4 output.mp4 --scale 4" -ForegroundColor White

Write-Host "`n  방법 2 - 어디서든 사용 (권장):" -ForegroundColor Yellow
Write-Host "    1. 새 명령 프롬프트 열기" -ForegroundColor White
Write-Host "    2. add-to-path.bat 실행" -ForegroundColor White
Write-Host "    3. upscaler image photo.jpg photo_4k.jpg" -ForegroundColor White

Write-Host "`n  방법 3 - PowerShell에서:" -ForegroundColor Yellow
Write-Host "    .\upscaler.ps1 image input.jpg output.jpg" -ForegroundColor White

Write-Host "`n  유용한 명령어:" -ForegroundColor Cyan
Write-Host "    upscaler --help    (도움말 보기)" -ForegroundColor White
Write-Host "    upscaler doctor    (시스템 진단)" -ForegroundColor White
Write-Host "    upscaler models --list  (모델 목록)`n" -ForegroundColor White

Write-Host "`n종료하려면 Enter를 누르세요..." -ForegroundColor DarkGray
Read-Host