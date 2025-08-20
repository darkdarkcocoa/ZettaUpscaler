import cv2
import numpy as np
import logging
import time
from pathlib import Path
from typing import Optional
from tqdm import tqdm

from ..backends import get_backend
from ..models import ModelManager
from ..utils.display_utils import (
    display_processing_start, display_processing_complete,
    display_backend_info, print_info, print_success, print_warning
)


logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process single images for upscaling."""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.backend = None
        self.model_manager = ModelManager()
    
    def process(self, input_path: str, output_path: str) -> None:
        """Process a single image."""
        start_time = time.time()
        
        # Display processing start information
        display_processing_start(input_path, output_path, "IMAGE", **self.kwargs)
        
        logger.info(f"Processing image: {input_path} -> {output_path}")
        
        # Validate input
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Load image with unchanged color
        image_bgr = cv2.imread(str(input_file), cv2.IMREAD_COLOR)
        if image_bgr is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        # Display input image information
        height, width, channels = image_bgr.shape
        print_info("Input Resolution", f"{width} x {height}", indent=2)
        print_info("Color Channels", f"{channels} channels", indent=2)
        
        # Try RGB format instead of BGR - maybe the model expects RGB after all
        image_for_processing = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        # Get backend
        self.backend = get_backend(**self.kwargs)
        
        # Display backend information
        backend_info = {
            'device': getattr(self.backend, 'device', 'CPU'),
            'cuda_available': getattr(self.backend, 'cuda_available', False)
        }
        display_backend_info(self.backend.__class__.__name__, backend_info)
        
        # Calculate output dimensions
        scale = self.kwargs.get('scale', 4)
        out_width = width * scale
        out_height = height * scale
        print_info("Output Resolution", f"{out_width} x {out_height}", indent=2)
        print_info("Upscale Factor", f"{scale}x", indent=2)
        
        # Process image
        with self.backend:
            logger.info(f"Upscaling with backend: {self.backend.__class__.__name__}")
            print_success(f"Backend initialized: {self.backend.__class__.__name__}")
            
            # Setup progress bar
            progress_format = self.kwargs.get('progress', 'bar')
            if progress_format == 'bar':
                pbar = tqdm(total=1, desc="Upscaling in progress", unit="image")
            
            try:
                # Upscale
                upscaled_bgr = self.backend.upscale(image_for_processing)
                
                # Optional: Match histogram to preserve original color tone
                preserve_tone = self.kwargs.get('preserve_tone', True)
                if preserve_tone:
                    try:
                        from ..utils.color_correction import match_histogram
                        # Resize original for histogram matching
                        h_up, w_up = upscaled_bgr.shape[:2]
                        original_resized = cv2.resize(image_for_processing, (w_up, h_up), interpolation=cv2.INTER_LINEAR)
                        upscaled_bgr = match_histogram(upscaled_bgr, original_resized)
                        logger.info("Applied histogram matching to preserve color tone")
                    except Exception as e:
                        logger.warning(f"Could not apply histogram matching: {e}")
                
                # Face enhancement if requested
                if self.kwargs.get('face_enhance', False):
                    upscaled_bgr = self._enhance_faces(upscaled_bgr)
                
                # Convert RGB back to BGR for OpenCV saving
                upscaled_bgr = cv2.cvtColor(upscaled_bgr, cv2.COLOR_RGB2BGR)
                
                # Save result with high quality
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Use high quality settings for PNG/JPEG
                if str(output_file).lower().endswith('.png'):
                    success = cv2.imwrite(str(output_file), upscaled_bgr, [cv2.IMWRITE_PNG_COMPRESSION, 0])
                elif str(output_file).lower().endswith(('.jpg', '.jpeg')):
                    success = cv2.imwrite(str(output_file), upscaled_bgr, [cv2.IMWRITE_JPEG_QUALITY, 100])
                else:
                    success = cv2.imwrite(str(output_file), upscaled_bgr)
                if not success:
                    raise RuntimeError(f"Failed to save image: {output_path}")
                
                if progress_format == 'bar':
                    pbar.update(1)
                    pbar.close()
                elif progress_format == 'json':
                    print(f'{{"status": "completed", "progress": 1.0, "message": "Image upscaling completed"}}')
                
                logger.info(f"Image upscaling completed: {output_path}")
                
                # Display completion information
                end_time = time.time()
                self.kwargs['backend_used'] = self.backend.__class__.__name__
                display_processing_complete(input_path, output_path, "IMAGE", 
                                           start_time, end_time, **self.kwargs)
                
            except Exception as e:
                if progress_format == 'bar' and 'pbar' in locals():
                    pbar.close()
                raise e
    
    def _enhance_faces(self, image: np.ndarray) -> np.ndarray:
        """Enhance faces using GFPGAN."""
        try:
            # This is a placeholder - would need actual GFPGAN implementation
            logger.warning("Face enhancement not yet implemented")
            return image
            
        except Exception as e:
            logger.warning(f"Face enhancement failed: {e}")
            return image