# 🚀 ZettaUpscaler

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CUDA](https://img.shields.io/badge/CUDA-12.1-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Real-ESRGAN 기반 고성능 AI 이미지/영상 업스케일링 도구. NVIDIA GPU 가속으로 최대 4배 해상도 업스케일링 지원.

## ✨ 주요 기능

- 🎨 **AI 업스케일링**: Real-ESRGAN 모델로 고품질 업스케일링
- 🎮 **GPU 가속**: NVIDIA GPU 자동 감지 및 최적화 (FP16 기본 활성화)
- 📹 **영상 지원**: 오디오 보존하며 전체 영상 처리
- 🖼️ **배치 처리**: 여러 이미지 효율적 처리
- 🔧 **다양한 모델**: 사진, 애니메이션, 일반 콘텐츠용 모델 선택
- 💻 **크로스 플랫폼**: Windows 지원, CPU 폴백 기능

## 🚀 빠른 시작 (Windows)

### 1️⃣ 설치 (1분 완성!)

```bash
# 1. 저장소 클론
git clone https://github.com/username/ZettaUpscaler.git
cd ZettaUpscaler

# 2. 자동 설치 실행 (관리자 권한 필요)
# 마우스 우클릭 → "관리자로 실행"
install.bat

# PowerShell 선호시:
powershell -ExecutionPolicy Bypass -File install.ps1
```

**install.bat가 자동으로 설치하는 항목:**
- Python 3.12 (없는 경우)
- FFmpeg
- Python 가상환경
- 모든 필수 패키지 (PyTorch, Real-ESRGAN 등)
- 환경변수 안전 설정

### 2️⃣ 사용법

설치 완료 후 `upscaler.bat`로 실행:

```bash
# 이미지 업스케일링 (4배)
upscaler image input.jpg output.jpg --scale 4

# 2배로 업스케일링 (더 빠름)
upscaler image photo.jpg photo_2x.jpg --scale 2

# 영상 업스케일링 (오디오 포함)
upscaler video input.mp4 output.mp4 --scale 4

# GPU 가속 확인
upscaler doctor
```

### 3️⃣ 어디서든 사용하기

새 명령 프롬프트에서:
```bash
# PATH에 추가 (현재 세션만)
add-to-path.bat

# 이제 어디서든 사용 가능!
upscaler image C:\Photos\vacation.jpg C:\Photos\vacation_4k.jpg
```

## 📊 성능

RTX 4060 Ti 기준 (1080p → 4K):
- **이미지** (1920×1080): 약 1.5-2초
- **영상** (1080p, 1분): 약 3-5분

RTX 4090 기준:
- 약 30-40% 더 빠름

## 🛠️ 고급 옵션

```bash
# 모든 옵션 보기
upscaler --help

# 사용 가능한 모델 확인
upscaler models --list

# 시스템 진단
upscaler doctor
```

### 주요 옵션
- `--scale`: 업스케일 배율 (2 또는 4, 기본값: 4)
- `--model`: 사용할 모델 선택
- `--fp16`: GPU 메모리 절약 (기본: 활성화)
- `--tile`: 타일 크기 (메모리 부족시 조정)
- `--face-enhance`: 얼굴 향상 기능

## 🎯 사용 예시

### 사진 고화질화
```bash
upscaler image family_photo.jpg family_photo_hd.jpg --model realesrgan-x4plus
```

### 애니메이션 업스케일
```bash
upscaler image anime.png anime_4k.png --model realesrgan-x4plus-anime
```

### 영상 업스케일 (오디오 포함)
```bash
upscaler video vacation.mp4 vacation_4k.mp4 --scale 4 --copy-audio
```

## ⚠️ 주의사항

1. **Python 버전**: Python 3.12 필수 (3.10/3.11은 호환성 문제 발생)
2. **GPU 메모리**: 4K 업스케일시 최소 6GB VRAM 권장
3. **디스크 공간**: 영상 처리시 충분한 임시 공간 필요
4. **환경변수**: setx 사용 금지 (PATH 손실 위험)

## 🆘 문제 해결

### "CUDA: Not Available" 표시
- GPU는 사용 중이지만 표시 오류일 수 있음
- `upscaler doctor`로 실제 상태 확인

### Python 버전 충돌 (ComfyUI 등)
```bash
# py launcher로 특정 버전 사용
py -3.12 -m pip install ...
```

### 메모리 부족
```bash
# 타일 크기 줄이기
upscaler image input.jpg output.jpg --tile 256
```

## 📦 모델 정보

| 모델 | 용도 | 배율 |
|-----|------|-----|
| `realesr-general-x4v3` | 일반용 (기본값) | 4x |
| `realesrgan-x4plus` | 사진 특화 | 4x |
| `realesrgan-x4plus-anime` | 애니메이션 특화 | 4x |

## 🤝 기여하기

버그 리포트나 기능 제안은 [Issues](https://github.com/username/ZettaUpscaler/issues)에 남겨주세요!

## 📄 라이선스

MIT License - 자유롭게 사용하세요.

## 🙏 감사의 말

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) - 핵심 업스케일링 모델
- [PyTorch](https://pytorch.org/) - 딥러닝 프레임워크

---

Made with ❤️ using Real-ESRGAN