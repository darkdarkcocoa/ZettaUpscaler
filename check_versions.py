import sys
print(f"Python: {sys.executable}")

try:
    import torch
    import torchvision
    print(f"PyTorch: {torch.__version__}")
    print(f"torchvision: {torchvision.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    print(f"Import error: {e}")

try:
    import basicsr
    print(f"basicsr: {basicsr.__version__}")

    # functional_tensor 확인
    try:
        from torchvision.transforms.functional_tensor import rgb_to_grayscale
        print("✅ functional_tensor import OK")
    except ImportError:
        try:
            from torchvision.transforms.functional import rgb_to_grayscale
            print("⚠️ functional_tensor 없음, functional 사용")
        except:
            print("❌ rgb_to_grayscale import 실패")
except:
    print("basicsr import 실패")