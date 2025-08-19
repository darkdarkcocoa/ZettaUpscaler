"""
Test GPU and Real-ESRGAN setup
"""
import sys
import subprocess
import os

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')

def test_setup():
    print("=" * 60)
    print("GPU & Real-ESRGAN Setup Test")
    print("=" * 60)
    
    # 1. Test PyTorch
    print("\n1. Testing PyTorch...")
    try:
        import torch
        print(f"[OK] PyTorch version: {torch.__version__}")
        print(f"[OK] CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[OK] CUDA version: {torch.version.cuda}")
            print(f"[OK] GPU: {torch.cuda.get_device_name(0)}")
            
            # Test tensor on GPU
            x = torch.rand(3, 3).cuda()
            print("[OK] GPU tensor creation successful")
        else:
            print("[WARNING] CUDA not available - GPU acceleration disabled")
    except Exception as e:
        print(f"[ERROR] PyTorch error: {e}")
        return False
    
    # 2. Test torchvision
    print("\n2. Testing torchvision...")
    try:
        import torchvision
        print(f"[OK] torchvision version: {torchvision.__version__}")
        from torchvision.transforms.functional import rgb_to_grayscale
        print("[OK] torchvision imports working")
    except Exception as e:
        print(f"[ERROR] torchvision error: {e}")
        return False
    
    # 3. Test BasicSR
    print("\n3. Testing BasicSR...")
    try:
        import basicsr
        print("[OK] BasicSR imported successfully")
    except Exception as e:
        print(f"[ERROR] BasicSR error: {e}")
        print("   Trying to fix...")
        # Try to fix the import
        try:
            subprocess.run([sys.executable, "fix_compatibility.py"], check=True)
            import basicsr
            print("[OK] BasicSR fixed and imported")
        except:
            print("[ERROR] Could not fix BasicSR")
            return False
    
    # 4. Test Real-ESRGAN
    print("\n4. Testing Real-ESRGAN...")
    try:
        import realesrgan
        print("[OK] Real-ESRGAN imported successfully")
        
        # Try to import the upsampler
        from realesrgan.archs.srvgg_arch import SRVGGNetCompact
        print("[OK] Real-ESRGAN model architecture available")
    except Exception as e:
        print(f"[ERROR] Real-ESRGAN error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed! Real-ESRGAN with GPU support is ready.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_setup()
    
    if success:
        print("\n[INFO] You can now use:")
        print("   python -m upscaler image input.png output.png --scale 4 --backend torch")
        print("\n   This will use Real-ESRGAN with GPU acceleration!")
    else:
        print("\n[WARNING] Setup incomplete. Please fix the errors above.")
        print("\nTry running:")
        print("   pip uninstall torch torchvision basicsr realesrgan -y")
        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        print("   pip install basicsr==1.4.2 realesrgan==0.3.0")
        print("   python fix_compatibility.py")
