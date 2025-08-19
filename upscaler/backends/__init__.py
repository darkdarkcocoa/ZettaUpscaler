import logging
from typing import Optional

from .torch_backend import TorchBackend
from .torch_backend_simple import SimpleTorchBackend
from .ncnn_backend import NcnnBackend


logger = logging.getLogger(__name__)


def get_backend(backend_name: str = 'auto', **kwargs):
    """Get the appropriate backend for upscaling."""
    
    if backend_name == 'auto':
        # Try backends in order of preference
        if NcnnBackend.is_available():
            logger.info("Using NCNN backend (Vulkan available)")
            return NcnnBackend(**kwargs)
        elif TorchBackend.is_available():
            logger.info("Using PyTorch backend with Real-ESRGAN")
            return TorchBackend(**kwargs)
        elif SimpleTorchBackend.is_available():
            logger.warning("Using simplified PyTorch backend (fallback mode)")
            logger.warning("For best quality, ensure Real-ESRGAN is properly installed")
            return SimpleTorchBackend(**kwargs)
        else:
            logger.warning("No backends available, using basic upscaling")
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