import torch
import torch.nn as nn
import numpy as np
import cv2
import logging
from pathlib import Path
from typing import Dict, Any

from .base import BaseBackend
from ..models import ModelManager
from .realesrgan_wrapper import load_realesrgan_model, upscale_image


logger = logging.getLogger(__name__)


class TorchBackend(BaseBackend):
    """PyTorch backend for Real-ESRGAN."""
    
    def __init__(self, device: str = None, **kwargs):
        super().__init__(**kwargs)
        
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        self.model_instance = None
        self.model_manager = ModelManager()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if PyTorch and Real-ESRGAN are available."""
        try:
            import torch
            # Also check if Real-ESRGAN can be imported
            try:
                import basicsr
                import realesrgan
                return True
            except ImportError:
                logger.debug("Real-ESRGAN not available, falling back")
                return False
        except ImportError:
            return False
    
    def initialize(self) -> None:
        """Initialize the model."""
        logger.info(f"Initializing PyTorch backend with device: {self.device}")
        
        # Download model if needed
        model_path = self.model_manager.get_model_path(self.model)
        if not model_path.exists():
            logger.info(f"Downloading model: {self.model}")
            self.model_manager.download_model(self.model)
        
        # Get scale from model info
        model_info = self.model_manager.models.get(self.model, {})
        scale = model_info.get('scale', self.scale)
        
        # Load model using the proper wrapper
        logger.info(f"Loading model {self.model} with scale {scale}")
        self.model_instance = load_realesrgan_model(
            model_path=str(model_path),
            device=self.device,
            scale=scale
        )
        
        # Apply fp16 if requested
        if self.fp16 and self.device == 'cuda':
            self.model_instance = self.model_instance.half()
            logger.info("Applied FP16 mode")
        
        # Set optimal settings for inference
        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image using Real-ESRGAN."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
        
        # Use auto-tiling
        tile_size = self.auto_tile_size()
        
        if tile_size > 0 and (image.shape[0] > tile_size or image.shape[1] > tile_size):
            return self._tile_image(image, tile_size, self.tile_overlap)
        else:
            return self._upscale_tile(image)
    
    def _upscale_tile(self, tile: np.ndarray) -> np.ndarray:
        """Upscale a single tile."""
        # Log input info
        logger.debug(f"Input tile shape: {tile.shape}, dtype: {tile.dtype}, range: [{tile.min()}, {tile.max()}]")
        
        # Get gamma value from kwargs
        gamma = self.kwargs.get('gamma', 0.9)  # Default to slightly brighter
        
        try:
            # Use the wrapper's upscale_image function which handles all color correction
            output = upscale_image(
                model=self.model_instance,
                img=tile,
                device=self.device,
                scale=self.scale,
                gamma=gamma
            )
            
            logger.debug(f"Final output shape: {output.shape}, dtype: {output.dtype}, range: [{output.min()}, {output.max()}]")
            
        except Exception as e:
            logger.error(f"Error during inference: {e}")
            # Return a properly sized black image as fallback
            h, w = tile.shape[:2]
            return np.zeros((h * self.scale, w * self.scale, 3), dtype=np.uint8)
        
        return output
    
    def auto_tile_size(self) -> int:
        """Calculate optimal tile size based on GPU memory."""
        if self.tile > 0:
            return self.tile
        
        if self.device == 'cpu':
            return 256  # Conservative for CPU
        
        try:
            # Get GPU memory info
            if torch.cuda.is_available():
                total_memory = torch.cuda.get_device_properties(0).total_memory
                allocated = torch.cuda.memory_allocated()
                free_memory = total_memory - allocated
                free_gb = free_memory / (1024**3)
                
                # Conservative estimates
                if free_gb > 8:
                    return 512
                elif free_gb > 4:
                    return 256
                elif free_gb > 2:
                    return 128
                else:
                    return 64
        except:
            pass
        
        return 256  # Default fallback
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information."""
        info = {}
        
        if self.device == 'cuda' and torch.cuda.is_available():
            info['device'] = 'cuda'
            info['total_mb'] = torch.cuda.get_device_properties(0).total_memory // (1024**2)
            info['allocated_mb'] = torch.cuda.memory_allocated() // (1024**2)
            info['available_mb'] = info['total_mb'] - info['allocated_mb']
        else:
            info['device'] = 'cpu'
            info['available_mb'] = 4000  # Conservative estimate
        
        return info
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.model_instance is not None:
            del self.model_instance
            self.model_instance = None
        
        if self.device == 'cuda' and torch.cuda.is_available():
            torch.cuda.empty_cache()