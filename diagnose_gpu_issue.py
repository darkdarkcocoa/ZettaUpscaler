#!/usr/bin/env python3
"""
ZettaUpscaler GPU/CUDA 문제 진단 스크립트
회사 PC에서 이 스크립트를 실행하여 정확한 문제를 파악합니다.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

print("=" * 80)
print("ZettaUpscaler GPU/CUDA 진단 스크립트")
print("=" * 80)
print()

# 가상환경 체크
if '.venv' not in sys.executable:
    print("⚠️  경고: 가상환경이 활성화되지 않았습니다!")
    print(f"   현재 Python: {sys.executable}")
    print()
    print("   다음 명령으로 가상환경을 활성화하세요:")
    print("   .venv\\Scripts\\activate")
    print()
    print("   또는 직접 실행:")
    print("   .venv\\Scripts\\python diagnose_gpu_issue.py")
    print("=" * 80)
    sys.exit(1)

# 1. 시스템 정보
print("[1] 시스템 정보")
print("-" * 40)
print(f"Python 버전: {sys.version}")
print(f"Python 경로: {sys.executable}")
print(f"OS: {platform.platform()}")
print()

# 2. GPU 정보 (nvidia-smi)
print("[2] NVIDIA GPU 정보")
print("-" * 40)
try:
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ nvidia-smi 성공!")
        # GPU 이름만 추출
        lines = result.stdout.split('\n')
        for line in lines:
            if 'NVIDIA' in line and '|' in line:
                print(f"GPU: {line.strip()}")
    else:
        print("❌ nvidia-smi 실패!")
except Exception as e:
    print(f"❌ nvidia-smi 에러: {e}")
print()

# 3. PyTorch 설치 확인
print("[3] PyTorch 설치 상태")
print("-" * 40)
try:
    import torch
    print(f"✅ PyTorch 버전: {torch.__version__}")
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA 버전: {torch.version.cuda}")
        print(f"cuDNN 버전: {torch.backends.cudnn.version()}")
        print(f"GPU 개수: {torch.cuda.device_count()}")
        print(f"현재 GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️  CUDA가 사용 불가능합니다!")

        # CPU 전용 PyTorch 설치 여부 확인
        if '+cpu' in torch.__version__:
            print("❌ PyTorch CPU 버전이 설치되어 있습니다!")
            print("   GPU를 사용하려면 CUDA 버전을 재설치해야 합니다.")
        else:
            print("PyTorch는 CUDA 버전이지만, CUDA를 찾을 수 없습니다.")

except ImportError as e:
    print(f"❌ PyTorch 설치 안됨: {e}")
print()

# 4. basicsr/realesrgan 설치 확인
print("[4] AI 패키지 설치 상태")
print("-" * 40)

# basicsr
try:
    import basicsr
    print(f"✅ basicsr 버전: {basicsr.__version__}")
except ImportError as e:
    print(f"❌ basicsr 설치 실패: {e}")
    # 상세 에러 확인
    try:
        subprocess.run([sys.executable, '-c', 'import basicsr'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"   상세 에러: {e.stderr}")

# realesrgan
try:
    import realesrgan
    print(f"✅ realesrgan 설치됨")

    # RealESRGANer import 테스트
    try:
        from realesrgan import RealESRGANer
        print("✅ RealESRGANer import 성공")
    except ImportError as e:
        print(f"❌ RealESRGANer import 실패: {e}")

except ImportError as e:
    print(f"❌ realesrgan 설치 실패: {e}")

# gfpgan (종속성)
try:
    import gfpgan
    try:
        print(f"✅ gfpgan 버전: {gfpgan.__version__}")
    except AttributeError:
        print("✅ gfpgan 설치됨 (버전 정보 없음)")
except ImportError as e:
    print(f"❌ gfpgan 설치 실패: {e}")

# facexlib (종속성)
try:
    import facexlib
    print(f"✅ facexlib 설치됨")
except ImportError as e:
    print(f"❌ facexlib 설치 실패: {e}")
print()

# 5. 백엔드 가용성 테스트
print("[5] 백엔드 가용성 테스트")
print("-" * 40)
sys.path.insert(0, str(Path(__file__).parent))

try:
    from upscaler.backends.torch_backend_official import TorchBackendOfficial, OFFICIAL_IMPLEMENTATION_AVAILABLE
    print(f"OFFICIAL_IMPLEMENTATION_AVAILABLE: {OFFICIAL_IMPLEMENTATION_AVAILABLE}")
    print(f"TorchBackendOfficial.is_available(): {TorchBackendOfficial.is_available()}")
except Exception as e:
    print(f"❌ TorchBackendOfficial import 실패: {e}")

try:
    from upscaler.backends.torch_backend import TorchBackend
    print(f"TorchBackend.is_available(): {TorchBackend.is_available()}")
except Exception as e:
    print(f"❌ TorchBackend import 실패: {e}")

try:
    from upscaler.backends import get_backend
    backend = get_backend('auto')
    print(f"자동 선택된 백엔드: {backend.__class__.__name__}")
except Exception as e:
    print(f"❌ get_backend 실패: {e}")
print()

# 6. 설치된 패키지 목록
print("[6] 설치된 관련 패키지")
print("-" * 40)
packages = ['torch', 'torchvision', 'basicsr', 'realesrgan', 'gfpgan', 'facexlib', 'numpy', 'opencv-python']
for pkg in packages:
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', pkg],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    print(f"{pkg}: {line.split(':')[1].strip()}")
                    break
        else:
            print(f"{pkg}: 설치 안됨")
    except:
        print(f"{pkg}: 확인 실패")
print()

# 7. 해결책 제안
print("[7] 문제 진단 및 해결책")
print("-" * 40)

problems = []
solutions = []

# PyTorch CPU 버전 문제
try:
    import torch
    if not torch.cuda.is_available() and '+cpu' in torch.__version__:
        problems.append("PyTorch CPU 버전이 설치되어 있음")
        solutions.append("""
1. 가상환경 활성화: .venv\\Scripts\\activate
2. PyTorch 제거: pip uninstall torch torchvision torchaudio -y
3. CUDA 버전 재설치: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
""")
except:
    pass

# basicsr/realesrgan 설치 문제
try:
    import basicsr
    import realesrgan
except ImportError:
    problems.append("basicsr 또는 realesrgan이 설치되지 않음")
    solutions.append("""
1. Visual Studio Build Tools 설치 확인 (C++ 컴파일러 필요)
2. 가상환경에서 재설치:
   pip install --no-cache-dir basicsr==1.4.2
   pip install --no-cache-dir realesrgan==0.3.0
3. 그래도 실패시:
   pip install --no-deps basicsr realesrgan
   pip install -r requirements.txt
""")

if problems:
    print("🔴 발견된 문제:")
    for i, problem in enumerate(problems, 1):
        print(f"  {i}. {problem}")

    print("\n💡 해결 방법:")
    for i, solution in enumerate(solutions, 1):
        print(f"\n[해결책 {i}]")
        print(solution)
else:
    print("✅ 특별한 문제를 발견하지 못했습니다.")
    print("   위의 로그를 공유해주시면 더 자세히 분석하겠습니다.")

print()
print("=" * 80)
print("진단 완료! 이 출력 결과를 복사해서 공유해주세요.")
print("=" * 80)