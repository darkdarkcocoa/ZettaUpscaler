"""
PyTorch backend using official Real-ESRGAN implementation
Based on Gemini DeepThink's solution
"""

import torch
import torch.nn as nn
import numpy as np
import cv2
import logging
from pathlib import Path
from typing import Dict, Any

from .base import BaseBackend
from ..models import ModelManager

logger = logging.getLogger(__name__)

# Official library imports
try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
    # SRVGGNetCompact for realesr-general models
    try:
        from basicsr.archs.srvgg_arch import SRVGGNetCompact
    except ImportError:
        from realesrgan.archs.srvgg_arch import SRVGGNetCompact
    OFFICIAL_IMPLEMENTATION_AVAILABLE = True
except ImportError as e:
    OFFICIAL_IMPLEMENTATION_AVAILABLE = False
    logger.warning(f"basicsr or realesrgan not installed. Official TorchBackend is unavailable. Error: {e}")


class TorchBackendOfficial(BaseBackend):
    """PyTorch backend for Real-ESRGAN (Official Implementation)."""
    
    def __init__(self, device: str = None, **kwargs):
        super().__init__(**kwargs)
        
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        self.cuda_available = (device == 'cuda' and torch.cuda.is_available())
        
        self.upscaler = None
        self.model_manager = ModelManager()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if official implementation is available"""
        return OFFICIAL_IMPLEMENTATION_AVAILABLE
    
    def initialize(self) -> None:
        # Re-check CUDA availability
        self.cuda_available = (self.device == 'cuda' and torch.cuda.is_available())
        if self.cuda_available:
            logger.info(f"CUDA is available! Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("CUDA not available or device set to CPU")
        """Initialize the model using RealESRGANer."""
        if not self.is_available():
            raise RuntimeError("Dependencies (basicsr, realesrgan) missing for Official TorchBackend.")

        logger.info(f"Initializing Official PyTorch backend (RealESRGANer) with device: {self.device}")
        
        # Download model if needed
        model_path = self.model_manager.get_model_path(self.model)
        if not model_path.exists():
            logger.info(f"Downloading model: {self.model}")
            self.model_manager.download_model(self.model)
        
        model_info = self.model_manager.models.get(self.model, {})
        scale = model_info.get('scale', self.scale)
        
        # 1. Define network architecture based on model type
        if 'general' in self.model.lower() or 'vgg' in self.model.lower():
            # For realesr-general-x4v3 (SRVGGNetCompact)
            logger.info("Using SRVGGNetCompact architecture")
            net = SRVGGNetCompact(
                num_in_ch=3, 
                num_out_ch=3, 
                num_feat=64, 
                num_conv=32, 
                upscale=scale, 
                act_type='prelu'
            )
        else:
            # For other Real-ESRGAN models (e.g., x4plus) (RRDBNet)
            logger.info("Using RRDBNet architecture")
            net = RRDBNet(
                num_in_ch=3, 
                num_out_ch=3, 
                num_feat=64, 
                num_block=23, 
                num_grow_ch=32, 
                scale=scale
            )

        # Determine tile size
        tile_size = self.tile if self.tile > 0 else self.auto_tile_size()

        # 2. Initialize RealESRGANer
        logger.info(f"Loading model {self.model} with scale {scale} using RealESRGANer. Tile size: {tile_size}")

        self.upscaler = RealESRGANer(
            scale=scale,
            model_path=str(model_path),
            model=net,
            tile=tile_size,
            tile_pad=self.tile_overlap,
            pre_pad=10,  # Default padding
            half=self.fp16 and self.device == 'cuda',
            device=self.device
        )
        
        # Optimization settings
        if self.device == 'cuda':
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
        
        logger.info("Official Real-ESRGAN backend initialized successfully")
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image using RealESRGANer."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
        
        # Official enhance method handles everything (tiling, data conversion, etc.)
        # Input: BGR uint8, Output: BGR uint8
        try:
            # Temporarily suppress stdout to hide "Tile X/Y" messages
            import sys
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            try:
                output, _ = self.upscaler.enhance(image, outscale=self.scale)
            finally:
                # Restore stdout
                sys.stdout = old_stdout
                
            logger.debug(f"Upscaled from {image.shape} to {output.shape}")
            return output
        except Exception as e:
            logger.error(f"Error during inference with RealESRGANer: {e}")
            # Return fallback image on failure
            h, w = image.shape[:2]
            return np.zeros((h * self.scale, w * self.scale, 3), dtype=np.uint8)
    
    def _upscale_tile(self, tile: np.ndarray) -> np.ndarray:
        """Required by base class but not used in official implementation"""
        return self.upscale(tile)
    
    def auto_tile_size(self) -> int:
        """Calculate optimal tile size based on GPU memory."""
        if self.tile > 0:
            return self.tile
        
        if self.device == 'cpu':
            return 512  # CPU can use larger tiles
        
        # GPU memory-based tile size
        try:
            if torch.cuda.is_available():
                free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
                free_gb = free_memory / (1024**3)
                
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
        """Clean up resources."""
        if self.upscaler is not None:
            del self.upscaler
            self.upscaler = None
        
        if self.device == 'cuda' and torch.cuda.is_available():
            torch.cuda.empty_cache()