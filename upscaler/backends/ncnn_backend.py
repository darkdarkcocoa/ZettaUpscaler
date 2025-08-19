import subprocess
import tempfile
import numpy as np
import cv2
import logging
from pathlib import Path
from typing import Dict, Any
import shutil

from .base import BaseBackend
from ..models import ModelManager


logger = logging.getLogger(__name__)


class NcnnBackend(BaseBackend):
    """NCNN backend using realesrgan-ncnn-vulkan binary."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.binary_path = None
        self.model_manager = ModelManager()
        self.temp_dir = None
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if NCNN binary is available."""
        # Check if realesrgan-ncnn-vulkan is in PATH
        return shutil.which('realesrgan-ncnn-vulkan') is not None
    
    def initialize(self) -> None:
        """Initialize the NCNN backend."""
        logger.info("Initializing NCNN backend")
        
        # Find binary
        self.binary_path = shutil.which('realesrgan-ncnn-vulkan')
        if not self.binary_path:
            raise RuntimeError("realesrgan-ncnn-vulkan binary not found in PATH")
        
        # Create temporary directory for processing
        self.temp_dir = tempfile.mkdtemp(prefix='upscaler_ncnn_')
        
        # Ensure model is available
        model_path = self.model_manager.get_ncnn_model_path(self.model)
        if not model_path.exists():
            logger.info(f"Downloading NCNN model: {self.model}")
            self.model_manager.download_ncnn_model(self.model)
    
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image using NCNN."""
        if not self._initialized:
            self.initialize()
            self._initialized = True
        
        return self._upscale_tile(image)
    
    def _upscale_tile(self, tile: np.ndarray) -> np.ndarray:
        """Upscale a single tile using NCNN binary."""
        import tempfile
        import os
        
        # Create temporary files
        input_file = os.path.join(self.temp_dir, 'input.png')
        output_file = os.path.join(self.temp_dir, 'output.png')
        
        # Save input image
        cv2.imwrite(input_file, cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))
        
        # Prepare command
        cmd = [
            self.binary_path,
            '-i', input_file,
            '-o', output_file,
            '-n', self._get_ncnn_model_name(),
            '-s', str(self.scale)
        ]
        
        # Add tiling options if specified
        if self.tile > 0:
            cmd.extend(['-t', str(self.tile)])
        
        # Run upscaling
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"NCNN upscaling failed: {result.stderr}")
            
            # Load result
            if not os.path.exists(output_file):
                raise RuntimeError("NCNN did not produce output file")
            
            output_bgr = cv2.imread(output_file)
            output_rgb = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
            
            # Clean up temp files
            os.remove(input_file)
            os.remove(output_file)
            
            return output_rgb
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("NCNN upscaling timed out")
    
    def _get_ncnn_model_name(self) -> str:
        """Map model name to NCNN model name."""
        # Map our model names to NCNN model names
        model_map = {
            'realesr-general-x4v3': 'realesr-general-x4v3',
            'realesrgan-x4plus': 'realesrgan-x4plus',
            'realesrgan-x4plus-anime': 'realesrgan-x4plus-anime',
            'real-cugan': 'real-cugan'
        }
        return model_map.get(self.model, self.model)
    
    def auto_tile_size(self) -> int:
        """Calculate optimal tile size for NCNN."""
        if self.tile > 0:
            return self.tile
        
        # NCNN is generally more memory efficient
        return 400  # Conservative default
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information."""
        return {
            'device': 'vulkan',
            'available_mb': 2000,  # Conservative estimate
            'backend': 'ncnn'
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None