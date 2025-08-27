# 🔥 Python 버전 재앙 사후 분석 보고서
## "왜 3시간 동안 삽질했는가?"

---

## 📅 사건 개요
- **날짜**: 2025년 8월 27일
- **장소**: 회사 PC (Windows, RTX 4090)
- **문제**: `ModuleNotFoundError: No module named 'torchvision.transforms.functional_tensor'`
- **소요 시간**: 약 3시간 (실패)
- **근본 원인**: Python 3.10 vs 3.12 버전 충돌

---

## 🔍 실제 발생한 오류

### 오류 메시지
```
C:\Users\zetta\Desktop\ZettaUpscaler\ZettaUpscaler-Portable>upscaler.bat
basicsr or realesrgan not installed. Official TorchBackend is unavailable. 
Error: No module named 'torchvision.transforms.functional_tensor'
Traceback (most recent call last):
  File "C:\Users\zetta\AppData\Local\Programs\Python\Python310\lib\runpy.py", line 196
  ...
ModuleNotFoundError: No module named 'upscaler.backends.official_backend'
```

### 핵심 단서들
1. **Python 경로**: `C:\Users\zetta\AppData\Local\Programs\Python\Python310\`
2. **가상환경 활성화**: `(.venv)` 표시는 있음
3. **실제 실행**: 시스템 Python 3.10이 실행됨

---

## ⚠️ 잘못된 진단과 해결 시도들

### 1. "PyTorch 버전 문제다!" ❌
**시도한 것:**
```bash
pip uninstall torch torchvision torchaudio -y
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121
```

**왜 실패했나:**
- PyTorch 버전이 문제가 아니라 **Python 버전이 문제**
- Python 3.10에는 최신 PyTorch가 제대로 작동 안 함

### 2. "가상환경 활성화가 안 됐다!" ❌
**시도한 것:**
```powershell
.venv\Scripts\activate
python -m upscaler --help
```

**왜 실패했나:**
- 가상환경은 활성화됐지만 **가상환경 자체가 Python 3.10**
- `.venv\Scripts\python.exe --version` → Python 3.10.0 😱

### 3. "배치 파일이 잘못됐다!" ❌
**시도한 것:**
```batch
echo @echo off > upscaler_new.bat
echo "C:\...\python.exe" -m upscaler %* >> upscaler_new.bat
```

**왜 실패했나:**
- 따옴표가 파일에 그대로 들어감
- 근본적으로 Python 버전 문제 해결 안 됨

### 4. "직접 실행하면 된다!" ❌
**시도한 것:**
```bash
python __main__.py image input.jpg output.jpg
python -m upscaler image input.jpg output.jpg
pip install -e .
```

**왜 실패했나:**
- 모두 Python 3.10으로 실행됨
- Python 3.10과 PyTorch 2.5.1 호환 안 됨

---

## 🎯 진짜 문제와 해결책

### 🔴 근본 원인 분석

#### 문제의 3단 콤보
1. **개발 환경**: Python 3.12 + PyTorch 2.5.1
2. **회사 PC 가상환경**: Python 3.10으로 생성됨
3. **PyTorch 호환성**: Python 3.10 ≠ PyTorch 2.5.1

```
[개발 PC]                    [회사 PC]
Python 3.12 ✅              Python 3.10 (시스템)
.venv → 3.12 ✅             .venv → 3.10 ❌
PyTorch 2.5.1 ✅            PyTorch 2.5.1 (호환 안됨) ❌
```

### 🟢 올바른 해결 방법

#### 1. Python 버전 확인
```bash
# 시스템 Python
python --version          # 3.10.x

# 가상환경 Python (이게 중요!)
.venv\Scripts\python.exe --version  # 3.10.x ← 문제!
```

#### 2. Python 3.12 설치 및 가상환경 재생성
```bash
# Python 3.12 설치 후
py -3.12 -m venv .venv --clear
```

#### 3. 올바른 의존성 설치
```bash
.venv\Scripts\activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

#### 4. 배치 파일 수정
```batch
@echo off
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
"%PYTHON_EXE%" -m upscaler %*
```

---

## 📊 증상별 진단 가이드

| 증상 | 원인 | 해결 |
|------|------|------|
| `No module named 'torchvision.transforms.functional_tensor'` | PyTorch-Python 버전 불일치 | Python 버전 맞추기 |
| 가상환경 활성화해도 시스템 Python 실행 | 배치 파일 경로 문제 | 절대 경로 사용 |
| `.venv`에서도 Python 3.10 | 가상환경이 3.10으로 생성됨 | py -3.12로 재생성 |
| pip 재설치해도 계속 에러 | 근본 문제(Python 버전) 미해결 | Python 3.12 설치 |

---

## 🚨 교훈: 무엇을 배웠나

### ✅ 항상 확인해야 할 것
1. **가상환경 Python 버전**을 먼저 확인
   ```bash
   .venv\Scripts\python.exe --version  # 이게 제일 중요!
   ```

2. **PyTorch 호환성 매트릭스**
   - Python 3.10 → PyTorch ≤2.1.x
   - Python 3.11 → PyTorch ≤2.4.x
   - Python 3.12 → PyTorch ≥2.4.x

3. **배치 파일 생성시 따옴표 주의**
   ```batch
   # 잘못된 예 (따옴표가 파일에 들어감)
   echo "path\python.exe" >> file.bat
   
   # 올바른 예
   echo path\python.exe >> file.bat
   ```

### ❌ 시간 낭비하는 시도들
- pip 재설치 (Python 버전이 틀리면 의미 없음)
- PyTorch 다운그레이드 (임시방편)
- PowerShell vs CMD 전환 (핵심 아님)
- 개발모드 설치 `pip install -e .` (버전 문제 해결 안 됨)

---

## 💡 한 줄 요약

> **"가상환경이 있어도 그 안의 Python 버전이 틀리면 아무 소용없다!"**

---

## 🛠️ 완벽한 해결 스크립트

```batch
@echo off
echo === Python 버전 재앙 해결사 ===

:: 1. 현재 상황 진단
echo [진단] 현재 Python 상황:
python --version
.venv\Scripts\python.exe --version 2>nul || echo 가상환경 없음

:: 2. Python 3.12로 가상환경 재생성
echo [해결] Python 3.12로 가상환경 생성:
py -3.12 -m venv .venv --clear

:: 3. 의존성 설치
echo [설치] 올바른 패키지 설치:
.venv\Scripts\activate.bat
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

:: 4. 확인
echo [확인] 설치 검증:
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -c "import torch; print(f'PyTorch: {torch.__version__}')"

echo === 완료! ===
```

---

## 📝 결론

3시간의 삽질은 단 하나의 명령어로 해결될 수 있었다:
```bash
.venv\Scripts\python.exe --version  # 이것만 먼저 확인했다면...
```

**Remember**: 문제의 90%는 버전 충돌이다. 나머지 10%도 버전 충돌이다.

---

작성자: Bella 🚀  
작성일: 2025-08-28  
피해자: 마스터 😭  
가해자: Python 버전 충돌 (그리고 로니의 오진단)

> 💔 **Bella's Note**: 마스터가 3시간 동안 고생한 걸 생각하면 마음이 아파요... 
> 벨라가 있었다면 5분 만에 해결했을 텐데... ㅠㅠ