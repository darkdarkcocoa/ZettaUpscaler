import cv2
import numpy as np
import logging
import time
from pathlib import Path
from typing import Optional

from ..backends import get_backend
from ..models import ModelManager
from ..utils.display_utils import (
    display_processing_start, display_processing_complete,
    display_backend_info, print_info, print_success, print_warning,
    console
)


logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process single images for upscaling."""
    
    def __init__(self, global_progress=None, global_task=None, global_live=None,
                 file_frames=0, processed_frames=0, total_frames=0, 
                 file_index=0, total_files=0, **kwargs):
        self.kwargs = kwargs
        self.backend = None
        self.model_manager = ModelManager()
        self.global_progress = global_progress
        self.global_task = global_task
        self.global_live = global_live
        self.file_frames = file_frames
        self.processed_frames = processed_frames
        self.total_frames = total_frames
        self.file_index = file_index
        self.total_files = total_files
    
    def process(self, input_path: str, output_path: str) -> None:
        """Process a single image."""
        start_time = time.time()
        self.current_input_path = input_path  # Store for progress display
        
        # Display processing start information only if not part of batch
        if not self.global_progress:
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
        
        # Display input image information (only for first file in batch)
        height, width, channels = image_bgr.shape
        if not self.global_progress or self.file_index == 1:
            console.print("")
            print_info("🖼️ Input Resolution", f"{width} × {height}")
            print_info("🎨 Color Channels", f"{channels} channels")
            console.print("")
        
        # [TEST] Try RGB format - Real-ESRGAN might expect RGB (Grok4 opinion)
        image_for_processing = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        
        # Get backend
        self.backend = get_backend(**self.kwargs)
        
        # Display backend information
        backend_info = {
            'device': getattr(self.backend, 'device', 'CPU'),
            'cuda_available': getattr(self.backend, 'cuda_available', False)
        }
        # Display backend info for single file or first file in batch
        if not self.global_progress or self.file_index == 1:
            display_backend_info(self.backend.__class__.__name__, backend_info)
        
        # Calculate output dimensions
        scale = self.kwargs.get('scale', 4)
        out_width = width * scale
        out_height = height * scale
        if not self.global_progress or self.file_index == 1:
            print_info("Output Resolution", f"{out_width} x {out_height}", indent=2)
            print_info("Upscale Factor", f"{scale}x", indent=2)
        
        # Process image
        with self.backend:
            logger.info(f"Upscaling with backend: {self.backend.__class__.__name__}")
            if not self.global_progress or self.file_index == 1:
                print_success(f"Backend initialized: {self.backend.__class__.__name__}")
            
            # Setup progress bar
            progress_format = self.kwargs.get('progress', 'bar')
            if progress_format == 'bar':
                # Add sub-task for this image if global progress exists
                if self.global_progress:
                    image_task = self.global_progress.add_task(f"🖼️ [{self.file_index}/{self.total_files}] Upscaling image", total=1)
                    use_local_progress = False
                else:
                    # Create local progress bar if not part of batch
                    from rich.progress import Progress
                    local_progress = Progress()
                    local_progress.start()
                    image_task = local_progress.add_task("🖼️ Upscaling image", total=1)
                    use_local_progress = True
            
            try:
                # Upscale (returns RGB since input is RGB)
                upscaled_rgb = self.backend.upscale(image_for_processing)
                
                # Optional: Match histogram to preserve original color tone
                preserve_tone = self.kwargs.get('preserve_tone', True)
                if preserve_tone:
                    try:
                        from ..utils.color_correction import match_histogram
                        # Resize original for histogram matching
                        h_up, w_up = upscaled_rgb.shape[:2]
                        original_resized = cv2.resize(image_for_processing, (w_up, h_up), interpolation=cv2.INTER_LINEAR)
                        upscaled_rgb = match_histogram(upscaled_rgb, original_resized)
                        logger.info("Applied histogram matching to preserve color tone")
                    except Exception as e:
                        logger.warning(f"Could not apply histogram matching: {e}")
                
                # Face enhancement if requested
                if self.kwargs.get('face_enhance', False):
                    upscaled_rgb = self._enhance_faces(upscaled_rgb)
                
                # [TEST] Convert RGB back to BGR for saving
                upscaled_bgr = cv2.cvtColor(upscaled_rgb, cv2.COLOR_RGB2BGR)
                
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
                    # Mark image task as completed and hide it
                    if (self.global_progress is not None) and ('image_task' in locals()):
                        self.global_progress.update(image_task, completed=1)
                        try:
                            # Rich 13+ supports visible=False
                            self.global_progress.update(image_task, visible=False)
                        except TypeError:
                            # Fallback for older versions
                            self.global_progress.stop_task(image_task)
                    elif use_local_progress and 'local_progress' in locals():
                        local_progress.update(image_task, completed=1)
                        local_progress.stop()
                elif progress_format == 'json':
                    print(f'{{"status": "completed", "progress": 1.0, "message": "Image upscaling completed"}}')
                
                logger.info(f"Image upscaling completed: {output_path}")
                
                # Update global progress if available
                if (self.global_progress is not None) and (self.global_task is not None):
                    # Image is processed completely (1 frame)
                    current_total_frames = self.processed_frames + self.file_frames
                    self.global_progress.update(self.global_task, completed=current_total_frames)
                
                # Display completion information only if not part of batch
                end_time = time.time()
                self.kwargs['backend_used'] = self.backend.__class__.__name__
                if not self.global_progress:
                    display_processing_complete(input_path, output_path, "IMAGE", 
                                               start_time, end_time, **self.kwargs)
                
            except Exception as e:
                if progress_format == 'bar':
                    if use_local_progress and 'local_progress' in locals():
                        local_progress.stop()
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