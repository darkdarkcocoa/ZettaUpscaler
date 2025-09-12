# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# 🚀 ZettaUpscaler 프로젝트 지침

## 📋 프로젝트 규칙

### Git 커밋 규칙
1. **커밋 메시지는 한글로 작성**
2. **간결하고 명확하게 변경사항만 기록**
3. **"Generated with Claude Code" 등의 서명 문구 금지** ❌
   - Co-Authored-By 금지
   - 불필요한 이모지 서명 금지
   - AI 도구 언급 금지

### 커밋 메시지 형식
```
동작: 간단한 설명

- 주요 변경사항 1
- 주요 변경사항 2
- 주요 변경사항 3
```

예시:
- ✅ 좋은 예: `수정: 프로그래스바 깜빡임 문제 해결`
- ❌ 나쁜 예: `수정: 프로그래스바 깜빡임 문제 해결 🤖 Generated with Claude Code`

## 🏗️ 프로젝트 아키텍처

### 핵심 구조
```
upscaler/
├── __main__.py        # python -m upscaler 실행 진입점
├── cli.py             # Click 기반 CLI 인터페이스 (image, video, all, doctor, models 명령어)
├── backends/          # 업스케일링 백엔드 구현
│   ├── torch_backend_official.py  # RealESRGANer 공식 구현 (우선순위 1)
│   ├── torch_backend.py          # PyTorch 백엔드 (우선순위 2)
│   └── ncnn_backend.py          # Vulkan 가속 백엔드 (우선순위 3)
├── processors/        # 이미지/비디오 처리 로직
│   ├── image_processor.py       # 이미지 업스케일링 핵심 로직
│   └── video_processor.py       # 비디오 프레임 추출/병합, 오디오 보존
├── models/           # 모델 다운로드 및 관리
│   └── manager.py    # 자동 모델 다운로드, 캐시 관리
└── utils/            # 유틸리티 모듈
    └── display_utils.py  # rich 라이브러리 기반 UI 컴포넌트
```

### 백엔드 시스템
- **자동 백엔드 선택**: `get_backend('auto')`가 가용한 최적 백엔드 자동 선택
- **TorchBackendOfficial**: Real-ESRGAN 공식 RealESRGANer 사용 (최고 품질)
- **TorchBackend**: 아키텍처 자동 감지 기능 포함
- **NcnnBackend**: Vulkan 지원시 사용 (경량화)

### 주요 모델
- `realesr-general-x4v3`: 일반용 기본 모델
- `realesrgan-x4plus`: 사진 특화
- `realesrgan-x4plus-anime`: 애니메이션 특화

## 🛠️ 개발 환경

### 필수 요구사항
- Python 3.10 이상 (3.12 권장)
- CUDA 지원 GPU (선택사항, CPU 폴백 지원)
- Windows Terminal (프로그래스바 최적화)
- FFmpeg (비디오 처리용)

### 빌드 및 실행 명령
```bash
# 가상환경 설정 (Windows)
python -m venv .venv
.\.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 직접 실행
python -m upscaler image input.jpg output.jpg --scale 4
python -m upscaler video input.mp4 output.mp4 --scale 4

# 폴더 일괄 처리 (NEW!)
python -m upscaler all
python -m upscaler all --type video --recursive
python -m upscaler all --dry-run

# 배치 파일로 실행 (Windows)
upscale image input.jpg output.jpg --scale 4
upscale all --type image

# 시스템 진단
python -m upscaler doctor

# 모델 목록
python -m upscaler models --list
```

### 패키징
```bash
# pip 패키지로 설치
pip install -e .

# 배포용 패키지 빌드
python setup.py sdist bdist_wheel
```

## 📝 구현 세부사항

### 프로그래스바 관련
- rich 라이브러리 사용, `auto_refresh=False`로 깜빡임 해결
- Windows Terminal OSC 9;4 시퀀스로 탭 진행률 표시
- `display_utils.py`에서 모든 UI 컴포넌트 중앙 관리

### 비디오 처리 특징
- FFmpeg으로 프레임 추출/병합
- 오디오 스트림 자동 보존 (`--copy-audio` 기본값)
- 임시 파일은 작업 디렉토리의 `.tmp_frames/` 폴더 사용

### 모델 관리
- 모델은 `~/.cache/realesrgan/` 또는 `%USERPROFILE%\.cache\realesrgan\`에 자동 다운로드
- SHA256 체크섬 검증 포함
- 손상된 모델 자동 재다운로드