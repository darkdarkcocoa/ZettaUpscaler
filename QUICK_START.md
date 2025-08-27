# 🚀 ZettaUpscaler 빠른 시작 가이드

## 📦 설치 (1분 완성!)

### Windows에서 설치
1. 프로젝트를 다운로드하거나 clone
2. **`install.bat`를 관리자로 실행** (우클릭 → 관리자로 실행)
3. 설치 완료! 🎉

설치 스크립트가 자동으로:
- ✅ Python 3.12 설치 (없는 경우)
- ✅ FFmpeg 설치
- ✅ 가상환경 생성
- ✅ 모든 의존성 설치
- ✅ 환경변수 설정
- ✅ GPU 자동 감지

## 🎯 사용법

### 이미지 업스케일링
```bash
# 기본 사용법 (4배 확대)
upscaler image input.jpg output.jpg

# 2배 확대
upscaler image input.png output.png --scale 2

# 특정 모델 사용
upscaler image photo.jpg photo_hd.jpg --model realesrgan-x4plus
```

### 비디오 업스케일링
```bash
# 오디오 포함 비디오 업스케일링
upscaler video input.mp4 output.mp4 --copy-audio

# 특정 프레임레이트로 출력
upscaler video input.mp4 output.mp4 --fps 60
```

## 🛠️ 유용한 명령어

```bash
# 도움말 보기
upscaler --help

# 시스템 진단 (GPU, 모델 확인)
upscaler doctor

# 모델 목록 보기
upscaler models --list

# 특정 모델 다운로드
upscaler models --download realesrgan-x4plus-anime
```

## 🎨 사용 가능한 모델

| 모델명 | 용도 | 특징 |
|--------|------|------|
| `realesr-general-x4v3` | 일반 (기본값) | 빠르고 균형잡힌 품질 |
| `realesrgan-x4plus` | 사진 | 자연스러운 텍스처 |
| `realesrgan-x4plus-anime` | 애니메이션 | 선명한 라인, 애니 스타일 |
| `gfpgan-1.4` | 얼굴 보정 | 얼굴 향상 특화 |

## ⚡ Pro Tips

1. **GPU 가속**: NVIDIA GPU가 있으면 자동으로 GPU 가속 사용
2. **메모리 부족시**: `--tile 256` 옵션으로 타일 크기 줄이기
3. **속도 우선**: `--fp16` 옵션으로 반정밀도 사용
4. **품질 우선**: `--model realesrgan-x4plus` 사용

## ❓ 문제 해결

### "python이 인식되지 않습니다"
→ 새 명령 프롬프트 열기 (환경변수 적용)

### "CUDA out of memory"
→ `--tile 128` 또는 `--fp16` 옵션 사용

### FFmpeg 오류
→ `install.bat` 다시 실행하여 FFmpeg 재설치

---
더 자세한 정보는 [README.md](README.md)를 참고하세요!