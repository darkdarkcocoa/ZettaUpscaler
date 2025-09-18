#!/usr/bin/env python3
"""
BasicSR torchvision 호환성 패치
torchvision.transforms.functional_tensor 모듈 문제 해결
"""

import os
import sys
import site

print("BasicSR 호환성 패치 시작...")
print("-" * 60)

# 가상환경 체크
if '.venv' not in sys.executable:
    print("❌ 가상환경이 활성화되지 않았습니다!")
    print("   .venv\\Scripts\\activate 실행 후 다시 시도하세요.")
    sys.exit(1)

try:
    # basicsr 찾기
    import basicsr
    basicsr_path = os.path.dirname(basicsr.__file__)
    print(f"✅ basicsr 경로: {basicsr_path}")

    # degradations.py 파일 찾기
    degradations_file = os.path.join(basicsr_path, "data", "degradations.py")

    if os.path.exists(degradations_file):
        print(f"✅ degradations.py 파일 발견")

        # 파일 읽기
        with open(degradations_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 패치 필요 여부 확인
        if "torchvision.transforms.functional_tensor" in content:
            print("⚠️  패치가 필요합니다!")

            # 백업
            backup_file = degradations_file + ".backup"
            if not os.path.exists(backup_file):
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 백업 생성: {backup_file}")

            # 패치 적용
            # 방법 1: functional_tensor -> functional로 변경
            patched_content = content.replace(
                "from torchvision.transforms.functional_tensor import rgb_to_grayscale",
                "from torchvision.transforms.functional import rgb_to_grayscale"
            )

            # 파일 쓰기
            with open(degradations_file, 'w', encoding='utf-8') as f:
                f.write(patched_content)

            print("✅ 패치 완료!")
        else:
            print("✅ 이미 패치되었거나 패치가 필요하지 않습니다.")
    else:
        print(f"❌ degradations.py 파일을 찾을 수 없습니다: {degradations_file}")

except ImportError:
    print("❌ basicsr이 설치되지 않았습니다.")
    sys.exit(1)

# 테스트
print("\n테스트 중...")
print("-" * 60)

try:
    import basicsr
    print("✅ basicsr import 성공!")

    try:
        import basicsr.data.degradations
        print("✅ basicsr.data.degradations import 성공!")
    except Exception as e:
        print(f"❌ degradations import 실패: {e}")

except Exception as e:
    print(f"❌ basicsr import 실패: {e}")

try:
    import realesrgan
    from realesrgan import RealESRGANer
    print("✅ realesrgan import 성공!")
except Exception as e:
    print(f"❌ realesrgan import 실패: {e}")

# 백엔드 테스트
try:
    sys.path.insert(0, '.')
    from upscaler.backends import get_backend
    backend = get_backend('auto')
    print(f"✅ 백엔드 선택: {backend.__class__.__name__}")
except Exception as e:
    print(f"❌ 백엔드 테스트 실패: {e}")

print("\n패치 완료! 이제 프로그램을 실행해보세요.")