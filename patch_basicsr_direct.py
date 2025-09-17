#!/usr/bin/env python3
"""
BasicSR 직접 패치 스크립트
import 없이 파일 직접 수정
"""

import os
import sys
from pathlib import Path

print("BasicSR 직접 패치 시작...")
print("-" * 60)

# 가상환경 체크
if '.venv' not in sys.executable:
    print("❌ 가상환경이 활성화되지 않았습니다!")
    sys.exit(1)

# site-packages 경로 찾기
venv_path = Path(sys.executable).parent.parent
site_packages = venv_path / "Lib" / "site-packages"

print(f"📁 site-packages 경로: {site_packages}")

# basicsr 폴더 찾기
basicsr_path = site_packages / "basicsr"
if not basicsr_path.exists():
    print("❌ basicsr 폴더를 찾을 수 없습니다!")
    print("   ultimate_fix.bat을 실행하세요.")
    sys.exit(1)

print(f"✅ basicsr 경로: {basicsr_path}")

# degradations.py 파일 경로
degradations_file = basicsr_path / "data" / "degradations.py"

if not degradations_file.exists():
    print(f"❌ degradations.py 파일을 찾을 수 없습니다: {degradations_file}")
    sys.exit(1)

print(f"📄 패치 대상 파일: {degradations_file}")

# 파일 읽기
try:
    with open(degradations_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print("✅ 파일 읽기 성공")
except Exception as e:
    print(f"❌ 파일 읽기 실패: {e}")
    sys.exit(1)

# 백업 생성
backup_file = str(degradations_file) + ".backup"
if not os.path.exists(backup_file):
    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 백업 생성: {backup_file}")
    except Exception as e:
        print(f"⚠️  백업 생성 실패: {e}")

# 패치 적용
original_line = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
patched_line = "from torchvision.transforms.functional import rgb_to_grayscale"

if original_line in content:
    print("🔧 패치 적용 중...")
    patched_content = content.replace(original_line, patched_line)

    try:
        with open(degradations_file, 'w', encoding='utf-8') as f:
            f.write(patched_content)
        print("✅ 패치 완료!")
    except Exception as e:
        print(f"❌ 패치 실패: {e}")
        sys.exit(1)
else:
    print("ℹ️  이미 패치되었거나 다른 버전입니다.")

# 간단한 테스트
print("\n테스트 중...")
print("-" * 60)

# basicsr import 테스트
test_cmd = f'"{sys.executable}" -c "import basicsr; print(\'✅ basicsr import 성공!\')"'
result = os.system(test_cmd)

if result != 0:
    print("⚠️  basicsr import가 여전히 실패합니다.")
    print("   ultimate_fix.bat을 실행하는 것을 권장합니다.")
else:
    # 백엔드 테스트
    print("\n백엔드 테스트...")
    test_cmd2 = f'"{sys.executable}" -c "import sys; sys.path.insert(0, \'.\'); from upscaler.backends import get_backend; b = get_backend(\'auto\'); print(f\'✅ 활성화된 백엔드: {{b.__class__.__name__}}\')"'
    os.system(test_cmd2)

print("\n패치 프로세스 완료!")