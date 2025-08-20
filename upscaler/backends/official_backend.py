"""Official Real-ESRGAN backend using basicsr"""

import torch
import numpy as np
import cv2
import logging
from pathlib import Path

from .base import BaseBackend
from ..models import ModelManager

logger = logging.getLogger(__name__)

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
    OFFICIAL_AVAILABLE = True
except ImportError:
    OFFICIAL_AVAILABLE = False
    logger.warning("Official Real-ESRGAN not available")


class OfficialBackend(BaseBackend):
    """Official Real-ESRGAN backend using basicsr"""
    
    def __init__(self, device: str = None, **kwargs):
        super().__init__(**kwargs)
        
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        self.upsampler = None
        self.model_manager = ModelManager()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if official Real-ESRGAN is available"""
        return OFFICIAL_AVAILABLE
    
    def initialize(self) -> None:
        """Initialize the official Real-ESRGAN model"""
        logger.info(f"Initializing Official Real-ESRGAN backend with device: {self.device}")
        
        # Download model if needed
        model_path = self.model_manager.get_model_path(self.model)
        if not model_path.exists():
            logger.info(f"Downloading model: {self.model}")
            self.model_manager.download_model(self.model)
        
        # Get scale from model info
        model_info = self.model_manager.models.get(self.model, {})
        scale = model_info.get('scale', self.scale)
        
        # Create network architecture (RRDBNet for most models)
        logger.info(f"Creating RRDBNet architecture for scale {scale}")
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=scale
        )
        
        # Create Real-ESRGANer instance
        self.upsampler = RealESRGANer(
            scale=scale,
            model_path=str(model_path),
            model=model,
            tile=self.tile if self.tile > 0 else 0,
            tile_pad=self.tile_overlap,
            pre_pad=10,
            half=self.fp16 and self.device == 'cuda',
            device=self.device
        )
        
        logger.info("Official Real-ESRGAN initialized successfully")
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image using official Real-ESRGAN"""
        if not self._initialized:
            self.initialize()
            self._initialized = True
        
        # The official enhance() expects BGR uint8 input
        # Our input is RGB from image_processor, so convert
        if image.dtype != np.uint8:
            image = np.clip(image, 0, 255).astype(np.uint8)
        
        # Convert RGB to BGR for official Real-ESRGAN
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Use official enhance
        try:
            output_bgr, _ = self.upsampler.enhance(image_bgr, outscale=self.scale)
            
            # Convert BGR back to RGB for consistency with our pipeline
            output_rgb = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
            
            logger.debug(f"Upscaled from {image.shape} to {output_rgb.shape}")
            return output_rgb
            
        except Exception as e:
            logger.error(f"Error during official Real-ESRGAN inference: {e}")
            # Return properly sized black image as fallback
            h, w = image.shape[:2]
            return np.zeros((h * self.scale, w * self.scale, 3), dtype=np.uint8)
    
    def _upscale_tile(self, tile: np.ndarray) -> np.ndarray:
        """Upscale a single tile (required by base class)"""
        return self.upscale(tile)
    
    def get_memory_info(self) -> dict:
        """Get memory usage information"""
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
        """Clean up resources"""
        if self.upsampler is not None:
            del self.upsampler
            self.upsampler = None
        
        if self.device == 'cuda' and torch.cuda.is_available():
            torch.cuda.empty_cache()