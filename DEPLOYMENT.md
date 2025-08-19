# 🚀 Upscaler 배포 가이드

## 📊 배포 옵션 비교

| 방법 | 파일 크기 | 장점 | 단점 | 추천 대상 |
|------|----------|------|------|----------|
| **PyInstaller (폴더)** | 500MB-1GB | 빠른 실행, 안정적 | 여러 파일 | 일반 사용자 |
| **PyInstaller (단일)** | 2-3GB | 파일 하나로 배포 | 크기 크고 느림 | 간단 배포 |
| **Nuitka** | 200-500MB | 가장 빠름, 작음 | 빌드 복잡 | 성능 중시 |
| **Python 패키지** | 10MB | 가장 작음 | Python 필요 | 개발자 |
| **Docker** | 3-4GB | 완벽한 격리 | Docker 필요 | 서버/클라우드 |

## 🎯 추천 배포 전략

### 1️⃣ **일반 사용자용 (Windows EXE)**

```bash
# 폴더 형태로 빌드 (추천)
D:\Workspace\Upscaler\build-exe.bat

# 결과물
dist/upscaler/
├── upscaler.exe         # 메인 실행 파일
├── torch/               # PyTorch 라이브러리
├── models/              # AI 모델 파일
└── *.dll               # 필요한 DLL들
```

**배포 방법:**
1. `dist/upscaler` 폴더 전체를 ZIP으로 압축
2. 사용자는 압축 해제 후 `upscaler.exe` 실행

---

### 2️⃣ **가벼운 설치 프로그램**

```batch
# Inno Setup 스크립트 생성
```

**setup.iss:**
```ini
[Setup]
AppName=AI Upscaler
AppVersion=1.0
DefaultDirName={pf}\Upscaler
DefaultGroupName=AI Upscaler
OutputBaseFilename=UpscalerSetup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\upscaler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\AI Upscaler"; Filename: "{app}\upscaler.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\upscaler.exe"; Parameters: "--help"; Flags: postinstall nowait
```

---

### 3️⃣ **고성능 배포 (Nuitka)**

```bash
# Nuitka 설치
pip install nuitka

# 빌드 (C++ 컴파일)
python -m nuitka --standalone --onefile --windows-console-mode=force --enable-plugin=torch --enable-plugin=numpy --include-package=upscaler --include-package=basicsr --include-package=realesrgan __main__.py
```

---

## 📦 배포 체크리스트

### **배포 전 필수 확인사항:**

- [ ] GPU/CPU 자동 감지 작동
- [ ] 모델 파일 포함 또는 자동 다운로드
- [ ] FFmpeg 포함 또는 설치 안내
- [ ] Windows Defender 예외 처리 안내
- [ ] 필요한 Visual C++ 재배포 패키지

### **포함해야 할 파일들:**

```
upscaler-portable/
├── upscaler.exe
├── README.txt
├── LICENSE.txt
├── models/
│   └── (모델은 첫 실행 시 자동 다운로드)
├── ffmpeg.exe (선택사항)
└── vc_redist.x64.exe (필요시)
```

---

## 🔧 빌드 자동화 스크립트

**build-release.bat:**
```batch
@echo off
:: 버전 설정
set VERSION=1.0.0

:: 빌드
call build-exe.bat

:: 릴리즈 폴더 생성
mkdir releases\upscaler-%VERSION%
xcopy /E /I dist\upscaler releases\upscaler-%VERSION%\

:: README 추가
echo AI Upscaler v%VERSION% > releases\upscaler-%VERSION%\README.txt
echo. >> releases\upscaler-%VERSION%\README.txt
echo Usage: upscaler.exe image input.jpg output.jpg --scale 4 >> releases\upscaler-%VERSION%\README.txt

:: ZIP 압축 (PowerShell 사용)
powershell Compress-Archive -Path "releases\upscaler-%VERSION%" -DestinationPath "releases\upscaler-%VERSION%-win64.zip"

echo Release created: releases\upscaler-%VERSION%-win64.zip
```

---

## 💡 모델 다운로드 전략

### **옵션 1: 모델 포함 (큰 파일)**
- 장점: 인터넷 없이 바로 사용
- 단점: 배포 파일 크기 증가 (+200MB)

### **옵션 2: 첫 실행 시 다운로드 (추천)**
- 장점: 작은 배포 파일 (500MB)
- 단점: 첫 실행 시 인터넷 필요

### **옵션 3: 선택적 다운로드**
```python
upscaler.exe models --download realesrgan-x4plus
upscaler.exe models --download realesrgan-x4plus-anime
```

---

## 🎨 GUI 버전 (선택사항)

**Tkinter GUI 추가:**
```python
# gui.py
import tkinter as tk
from tkinter import filedialog, ttk
import threading
from upscaler.processors import ImageProcessor

class UpscalerGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AI Upscaler")
        # ... GUI 코드
```

**Electron 웹 버전:**
```javascript
// 웹 기반 GUI
const { app, BrowserWindow } = require('electron')
// ... Electron 앱
```

---

## 📈 배포 후 업데이트

### **자동 업데이트 시스템:**
```python
# 버전 체크 및 업데이트
def check_update():
    current = "1.0.0"
    latest = get_latest_version()  # GitHub API
    if latest > current:
        download_update()
```

---

## 🚀 최종 추천

### **빠른 배포:** PyInstaller 폴더 방식
```bash
build-exe.bat
# dist/upscaler 폴더 ZIP 압축 후 배포
```

### **전문 배포:** Inno Setup 설치 프로그램
```bash
# 설치 프로그램 생성
iscc setup.iss
```

### **최적 성능:** Nuitka 컴파일
```bash
# C++ 컴파일로 최고 성능
python -m nuitka --standalone __main__.py
```
