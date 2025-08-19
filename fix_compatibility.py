"""
Fix compatibility issues with BasicSR and torchvision
"""
import os
import sys

def fix_basicsr_import():
    """Fix the import issue in basicsr degradations.py"""
    try:
        import site
        for site_path in site.getsitepackages():
            degradations_path = os.path.join(site_path, 'basicsr', 'data', 'degradations.py')
            
            if os.path.exists(degradations_path):
                print(f"Found degradations.py at: {degradations_path}")
                
                # Read the file
                with open(degradations_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace the problematic import
                old_import = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
                new_import = "from torchvision.transforms.functional import rgb_to_grayscale"
                
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    
                    # Write back
                    with open(degradations_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print("[OK] Fixed import issue in degradations.py")
                    return True
                else:
                    print("[INFO] Import already fixed or different version")
                    return True
        
        # Also check in current venv
        venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'Lib', 'site-packages')
        degradations_path = os.path.join(venv_path, 'basicsr', 'data', 'degradations.py')
        
        if os.path.exists(degradations_path):
            print(f"Found degradations.py in venv at: {degradations_path}")
            
            # Read the file
            with open(degradations_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the problematic import
            old_import = "from torchvision.transforms.functional_tensor import rgb_to_grayscale"
            new_import = "from torchvision.transforms.functional import rgb_to_grayscale"
            
            if old_import in content:
                content = content.replace(old_import, new_import)
                
                # Write back
                with open(degradations_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("[OK] Fixed import issue in degradations.py")
                return True
            else:
                print("[INFO] Import already fixed or different version")
                return True
        
        print("[ERROR] Could not find degradations.py at expected location")
        return False
            
    except Exception as e:
        print(f"[ERROR] Error fixing import: {e}")
        return False

def check_cuda():
    """Check CUDA availability"""
    try:
        import torch
        print(f"\n[INFO] PyTorch version: {torch.__version__}")
        print(f"[INFO] CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"[INFO] CUDA version: {torch.version.cuda}")
            print(f"[INFO] GPU count: {torch.cuda.device_count()}")
            print(f"[INFO] GPU name: {torch.cuda.get_device_name(0)}")
            
            # Test CUDA
            x = torch.rand(5, 3).cuda()
            print(f"[OK] CUDA test successful: Created tensor on GPU")
        else:
            print("[WARNING] CUDA not available - using CPU")
    except ImportError:
        print("[ERROR] PyTorch not installed")
    except Exception as e:
        print(f"[ERROR] Error checking CUDA: {e}")

def test_imports():
    """Test if all required imports work"""
    print("\n[INFO] Testing imports...")
    
    try:
        import torch
        print("[OK] torch imported successfully")
    except ImportError as e:
        print(f"[ERROR] torch import failed: {e}")
        return False
    
    try:
        import torchvision
        print("[OK] torchvision imported successfully")
    except ImportError as e:
        print(f"[ERROR] torchvision import failed: {e}")
        return False
    
    try:
        import basicsr
        print("[OK] basicsr imported successfully")
    except ImportError as e:
        print(f"[ERROR] basicsr import failed: {e}")
        return False
    
    try:
        import realesrgan
        print("[OK] realesrgan imported successfully")
    except ImportError as e:
        print(f"[ERROR] realesrgan import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Fixing compatibility issues...\n")
    
    # Fix the import issue
    fix_basicsr_import()
    
    # Check CUDA
    check_cuda()
    
    # Test imports
    if test_imports():
        print("\n[SUCCESS] All imports working! You can now use Real-ESRGAN with GPU acceleration.")
    else:
        print("\n[WARNING] Some imports still failing. You may need to reinstall packages.")
