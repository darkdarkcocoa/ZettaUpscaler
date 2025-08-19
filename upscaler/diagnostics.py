import platform
import sys
import subprocess
import shutil
import logging
from typing import Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class SystemDiagnostics:
    """System diagnostics for troubleshooting."""
    
    def __init__(self):
        pass
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive system diagnostics report."""
        
        report = {}
        
        # System information
        report['System'] = self._get_system_info()
        
        # Python environment
        report['Python'] = self._get_python_info()
        
        # Dependencies
        report['Dependencies'] = self._check_dependencies()
        
        # GPU information
        report['GPU'] = self._get_gpu_info()
        
        # FFmpeg information
        report['FFmpeg'] = self._get_ffmpeg_info()
        
        # Available models
        report['Models'] = self._get_model_info()
        
        # Backend availability
        report['Backends'] = self._get_backend_info()
        
        return report
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        return {
            'Platform': platform.platform(),
            'System': platform.system(),
            'Release': platform.release(),
            'Version': platform.version(),
            'Architecture': platform.architecture()[0],
            'Processor': platform.processor() or 'Unknown',
            'Machine': platform.machine()
        }
    
    def _get_python_info(self) -> Dict[str, str]:
        """Get Python environment information."""
        return {
            'Version': sys.version,
            'Executable': sys.executable,
            'Platform': sys.platform,
            'Implementation': platform.python_implementation(),
            'Compiler': platform.python_compiler()
        }
    
    def _check_dependencies(self) -> Dict[str, str]:
        """Check required dependencies."""
        dependencies = {}
        
        # Check key Python packages
        packages = [
            'torch', 'torchvision', 'cv2', 'PIL', 'numpy', 
            'tqdm', 'click', 'gdown', 'requests'
        ]
        
        for package in packages:
            try:
                if package == 'cv2':
                    import cv2
                    dependencies[package] = cv2.__version__
                elif package == 'PIL':
                    from PIL import Image
                    dependencies[package] = Image.__version__
                else:
                    module = __import__(package)
                    version = getattr(module, '__version__', 'Unknown')
                    dependencies[package] = version
            except ImportError:
                dependencies[package] = 'Not installed'
            except Exception as e:
                dependencies[package] = f'Error: {e}'
        
        return dependencies
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information."""
        gpu_info = {}
        
        # CUDA information
        try:
            import torch
            gpu_info['CUDA Available'] = torch.cuda.is_available()
            
            if torch.cuda.is_available():
                gpu_info['CUDA Version'] = torch.version.cuda
                gpu_info['cuDNN Version'] = torch.backends.cudnn.version()
                gpu_info['GPU Count'] = torch.cuda.device_count()
                
                for i in range(torch.cuda.device_count()):
                    props = torch.cuda.get_device_properties(i)
                    gpu_info[f'GPU {i}'] = {
                        'Name': props.name,
                        'Memory': f'{props.total_memory // 1024**2} MB',
                        'Compute Capability': f'{props.major}.{props.minor}',
                        'Multi Processors': props.multi_processor_count
                    }
        except ImportError:
            gpu_info['CUDA'] = 'PyTorch not installed'
        except Exception as e:
            gpu_info['CUDA'] = f'Error: {e}'
        
        # Check for other GPU APIs
        gpu_info['Vulkan'] = self._check_vulkan()
        
        return gpu_info
    
    def _check_vulkan(self) -> str:
        """Check Vulkan support."""
        try:
            # Try to find vulkan-1.dll or libvulkan.so
            if platform.system() == 'Windows':
                import ctypes
                try:
                    ctypes.CDLL('vulkan-1.dll')
                    return 'Available'
                except OSError:
                    return 'Not found'
            else:
                try:
                    import ctypes
                    ctypes.CDLL('libvulkan.so.1')
                    return 'Available'
                except OSError:
                    return 'Not found'
        except Exception as e:
            return f'Error checking: {e}'
    
    def _get_ffmpeg_info(self) -> Dict[str, str]:
        """Get FFmpeg information."""
        ffmpeg_info = {}
        
        # Check ffmpeg
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            try:
                result = subprocess.run(
                    [ffmpeg_path, '-version'], 
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    ffmpeg_info['ffmpeg'] = version_line
                else:
                    ffmpeg_info['ffmpeg'] = 'Error getting version'
            except Exception as e:
                ffmpeg_info['ffmpeg'] = f'Error: {e}'
        else:
            ffmpeg_info['ffmpeg'] = 'Not found in PATH'
        
        # Check ffprobe
        ffprobe_path = shutil.which('ffprobe')
        ffmpeg_info['ffprobe'] = 'Found' if ffprobe_path else 'Not found in PATH'
        
        return ffmpeg_info
    
    def _get_model_info(self) -> Dict[str, str]:
        """Get information about available models."""
        try:
            from .models import ModelManager
            
            manager = ModelManager()
            models = manager.list_available_models()
            
            model_info = {}
            for model_name in models:
                available = manager.is_model_available(model_name)
                model_info[model_name] = 'Downloaded' if available else 'Not downloaded'
            
            # Check cache directory
            cache_size = self._get_cache_size(manager.cache_dir)
            model_info['Cache Size'] = cache_size
            model_info['Cache Directory'] = str(manager.cache_dir)
            
            return model_info
            
        except Exception as e:
            return {'Error': str(e)}
    
    def _get_backend_info(self) -> Dict[str, str]:
        """Get backend availability information."""
        backend_info = {}
        
        try:
            from .backends import TorchBackend, NcnnBackend
            
            backend_info['PyTorch'] = 'Available' if TorchBackend.is_available() else 'Not available'
            backend_info['NCNN'] = 'Available' if NcnnBackend.is_available() else 'Not available'
            
            # Check realesrgan-ncnn-vulkan binary
            ncnn_binary = shutil.which('realesrgan-ncnn-vulkan')
            backend_info['NCNN Binary'] = 'Found' if ncnn_binary else 'Not found in PATH'
            
        except Exception as e:
            backend_info['Error'] = str(e)
        
        return backend_info
    
    def _get_cache_size(self, cache_dir: Path) -> str:
        """Get total size of cache directory."""
        try:
            total_size = 0
            for file_path in cache_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            # Convert to human readable format
            if total_size < 1024:
                return f'{total_size} B'
            elif total_size < 1024**2:
                return f'{total_size / 1024:.1f} KB'
            elif total_size < 1024**3:
                return f'{total_size / 1024**2:.1f} MB'
            else:
                return f'{total_size / 1024**3:.1f} GB'
                
        except Exception:
            return 'Unknown'