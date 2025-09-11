# 🤖 ZettaUpscaler 프로젝트 지침

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

## 🛠️ 개발 환경

### 필수 요구사항
- Python 3.10 이상 (3.12 권장)
- CUDA 지원 GPU (선택사항)
- Windows Terminal (프로그래스바 최적화)

### 테스트 명령
```bash
# 비디오 업스케일링 테스트
python -m upscaler video ani.mp4 output.mp4 --scale 4

# 이미지 업스케일링 테스트
python -m upscaler image input.jpg output.jpg --scale 4
```

## 📝 메모
- 프로그래스바 깜빡임 문제는 `auto_refresh=False`로 해결됨
- Windows Terminal에서 OSC 9;4 시퀀스로 탭 진행률 표시 가능