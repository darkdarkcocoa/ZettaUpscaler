from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, Optional, Tuple


class BaseBackend(ABC):
    """Base class for upscaling backends."""
    
    def __init__(self, model: str, scale: int = 4, tile: int = 0, 
                 tile_overlap: int = 32, fp16: bool = False, **kwargs):
        self.model = model
        self.scale = scale
        self.tile = tile
        self.tile_overlap = tile_overlap
        self.fp16 = fp16
        self.kwargs = kwargs
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the backend and load models."""
        pass
    
    @abstractmethod
    def upscale(self, image: np.ndarray) -> np.ndarray:
        """Upscale an image.
        
        Args:
            image: Input image in RGB format (H, W, 3)
            
        Returns:
            Upscaled image in RGB format
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass
    
    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Check if this backend is available."""
        pass
    
    @abstractmethod
    def get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage information."""
        pass
    
    def auto_tile_size(self) -> int:
        """Calculate optimal tile size based on available memory."""
        if self.tile > 0:
            return self.tile
        
        # Default heuristics - can be overridden by backends
        memory_info = self.get_memory_info()
        available_mb = memory_info.get('available', 4000)  # Default 4GB
        
        if available_mb > 8000:
            return 512
        elif available_mb > 4000:
            return 256
        elif available_mb > 2000:
            return 128
        else:
            return 64
    
    def _tile_image(self, image: np.ndarray, tile_size: int, overlap: int) -> np.ndarray:
        """Generic tiling implementation."""
        if tile_size == 0:
            # Process entire image
            return self._upscale_tile(image)
        
        h, w = image.shape[:2]
        scale = self.scale
        
        # Calculate output dimensions
        out_h, out_w = h * scale, w * scale
        output = np.zeros((out_h, out_w, 3), dtype=image.dtype)
        
        # Calculate tiles
        tiles_h = (h + tile_size - 1) // tile_size
        tiles_w = (w + tile_size - 1) // tile_size
        
        for i in range(tiles_h):
            for j in range(tiles_w):
                # Calculate tile boundaries with overlap
                y1 = max(0, i * tile_size - overlap)
                y2 = min(h, (i + 1) * tile_size + overlap)
                x1 = max(0, j * tile_size - overlap)
                x2 = min(w, (j + 1) * tile_size + overlap)
                
                # Extract tile
                tile = image[y1:y2, x1:x2]
                
                # Upscale tile
                upscaled_tile = self._upscale_tile(tile)
                
                # Calculate output position
                out_y1 = y1 * scale
                out_y2 = y2 * scale
                out_x1 = x1 * scale
                out_x2 = x2 * scale
                
                # Blend with existing output (simple averaging for overlaps)
                if overlap > 0:
                    # TODO: Implement proper blending
                    pass
                
                output[out_y1:out_y2, out_x1:out_x2] = upscaled_tile
        
        return output
    
    @abstractmethod
    def _upscale_tile(self, tile: np.ndarray) -> np.ndarray:
        """Upscale a single tile. Must be implemented by backends."""
        pass
    
    def __enter__(self):
        if not self._initialized:
            self.initialize()
            self._initialized = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()