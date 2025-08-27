# 📁 프로젝트 구조

## 🚀 사용자를 위한 파일들
- **`install.bat`** - 원클릭 설치 스크립트 (관리자로 실행)
- **`upscaler.bat`** - 메인 실행 파일 (설치 후 사용)
- **`QUICK_START.md`** - 빠른 시작 가이드
- **`README.md`** - 전체 설명서

## 📂 폴더 구조
```
ZettaUpscaler/
├── upscaler/           # 메인 Python 패키지
│   ├── backends/       # 백엔드 구현 (PyTorch, NCNN 등)
│   ├── processors/     # 이미지/비디오 처리기
│   ├── models/         # 모델 관리자
│   └── utils/          # 유틸리티 함수
├── scripts/            # 스크립트 모음
│   ├── dev/           # 개발자용 스크립트
│   └── user/          # 사용자용 스크립트
├── .venv/             # Python 가상환경 (자동 생성)
└── p2_upscaled.png    # 테스트 결과물 예시
```

## 🛠️ 개발자를 위한 파일들
- `scripts/dev/build-*.bat` - 실행파일 빌드 스크립트
- `requirements.txt` - Python 의존성 목록
- `setup.py` - 패키지 설정

## 🎯 핵심 명령어
```bash
# 설치
install.bat (관리자로 실행)

# 사용
upscaler image input.jpg output.jpg
upscaler video input.mp4 output.mp4
upscaler doctor (시스템 진단)
```