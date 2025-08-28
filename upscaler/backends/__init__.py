import logging
from typing import Optional

from .torch_backend import TorchBackend
from .torch_backend_simple import SimpleTorchBackend
from .torch_backend_official import TorchBackendOfficial
from .ncnn_backend import NcnnBackend
# from .official_backend import OfficialBackend  # 파일이 없어서 주석처리


logger = logging.getLogger(__name__)


def get_backend(backend_name: str = 'auto', **kwargs):
    """Get the appropriate backend for upscaling."""
    
    if backend_name == 'auto':
        # Try backends in order of preference
        # First try official implementation (Gemini DeepThink solution)
        if TorchBackendOfficial.is_available():
            logger.info("Using Official PyTorch backend (RealESRGANer)")
            return TorchBackendOfficial(**kwargs)
        # Then try improved TorchBackend with architecture detection
        elif TorchBackend.is_available():
            logger.info("Using PyTorch backend with architecture detection")
            return TorchBackend(**kwargs)
        elif NcnnBackend.is_available():
            logger.info("Using NCNN backend (Vulkan available)")
            return NcnnBackend(**kwargs)
        else:
            logger.warning("No AI backends available, using basic interpolation")
            return SimpleTorchBackend(device='cpu', **kwargs)
    
    elif backend_name == 'torch':
        if not TorchBackend.is_available():
            raise RuntimeError("PyTorch backend not available")
        return TorchBackend(**kwargs)
    
    elif backend_name == 'ncnn':
        if not NcnnBackend.is_available():
            raise RuntimeError("NCNN backend not available")
        return NcnnBackend(**kwargs)
    
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


__all__ = ['get_backend', 'TorchBackend', 'NcnnBackend']