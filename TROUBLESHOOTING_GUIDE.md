# 🔧 ZettaUpscaler Python 버전 충돌 해결 가이드

## 🎯 문제 상황
- **에러**: `ModuleNotFoundError: No module named 'torchvision.transforms'`
- **원인**: Python 3.10 (로컬) vs Python 3.12 (프로젝트) 버전 충돌
- **증상**: upscaler.bat 실행 시 로컬 Python을 사용해서 발생

---

## ✅ 해결 순서 (Step by Step)

### 📌 Step 1: 프로젝트 디렉토리로 이동
```cmd
cd D:\YourProject\ZettaUpscaler
dir
```

### 📌 Step 2: 현재 Python 상황 확인
```cmd
# 로컬 Python 확인
python --version
where python

# 가상환경 Python 확인 
.venv\Scripts\python.exe --version
```

**예상 결과:**
- 로컬: Python 3.10.x → `C:\Users\[사용자]\AppData\Local\Programs\Python\Python310\`
- 가상환경: Python 3.12.x → `D:\...\ZettaUpscaler\.venv\Scripts\`

### 📌 Step 3: 환경 수정 스크립트 실행
```cmd
fix_env.bat
```

**이 스크립트가 하는 일:**
1. Python 버전 체크
2. 가상환경 재생성 (필요시)
3. pip 업그레이드
4. PyTorch CUDA 12.1 버전 재설치
5. 모든 의존성 재설치
6. 설치 검증

⏰ **예상 시간**: 5-10분 (인터넷 속도에 따라)

### 📌 Step 4: 작동 확인
```cmd
# 기본 테스트
upscaler.bat --help

# Python 경로 확인 (중요!)
# "Using Python: D:\...\ZettaUpscaler\.venv\Scripts\python.exe" 가 나와야 함
# Python 3.12.x 버전이 표시되어야 함
```

### 📌 Step 5: 실제 테스트
```cmd
# 이미지 업스케일링 테스트
upscaler.bat image test.jpg output.jpg --scale 4

# GPU 사용 확인
upscaler.bat doctor
```

---

## 🚨 문제 발생 시 대처법

### Case 1: 여전히 Python 3.10 사용하는 경우
```cmd
# upscaler.bat 내용 확인
type upscaler.bat

# 직접 실행
.venv\Scripts\python.exe -m upscaler --help
```

### Case 2: Python 3.12가 없다는 메시지
```cmd
# Python 3.12 설치 필요
# 1. python.org에서 Python 3.12 다운로드
# 2. 설치 후:
py -3.12 -m venv .venv --clear
fix_env.bat
```

### Case 3: CUDA/GPU 관련 오류
```cmd
# GPU 상태 확인
nvidia-smi

# CPU 모드로 실행
upscaler.bat image input.jpg output.jpg --backend cpu
```

### Case 4: 권한 오류
```cmd
# 관리자 권한으로 CMD 실행
# 또는 PowerShell에서:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
python -m upscaler --help
```

---

## 📊 검증 체크리스트

✅ **성공 기준:**
- [ ] `upscaler.bat --help` 실행 시 도움말 표시
- [ ] Python 경로가 `.venv\Scripts\python.exe`로 표시
- [ ] Python 버전이 3.12.x로 표시
- [ ] GPU 사용 가능 (nvidia-smi 작동)
- [ ] 실제 이미지 업스케일링 성공

---

## 💡 핵심 포인트

1. **절대 경로 사용**: upscaler.bat이 반드시 `.venv\Scripts\python.exe`를 사용해야 함
2. **Python 버전 일치**: PyTorch는 Python 3.12용으로 설치되어야 함
3. **CUDA 버전**: RTX 4090은 CUDA 12.1 사용 권장

---

## 📞 추가 지원

문제가 지속되면:
1. 에러 메시지 전체를 캡처
2. `python --version`과 `.venv\Scripts\python.exe --version` 결과 확인
3. `pip list` 결과 확인

---

## 🎯 Quick Fix (긴급 해결법)

모든 게 실패하면 이것만 실행:
```cmd
# 가상환경 완전 재구성
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate.bat
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
.venv\Scripts\python.exe -m upscaler --help
```

---

작성자: Bella 🚀
작성일: 2025-08-28
문제: Python 3.10 vs 3.12 버전 충돌로 인한 ModuleNotFoundError