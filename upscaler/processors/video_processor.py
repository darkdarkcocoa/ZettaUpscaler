import subprocess
import sys
import cv2
import numpy as np
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
# from tqdm import tqdm  # Replaced with rich.progress
import tempfile
import os

from ..backends import get_backend
from ..models import ModelManager
from ..utils.video import get_video_info, get_ffmpeg_path, Y4MReader, Y4MWriter
from ..utils.display_utils import (
    display_processing_start, display_video_info, 
    display_processing_complete, display_backend_info,
    print_info, print_success, print_warning,
    create_progress, console, set_windows_terminal_progress
)


logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process videos for upscaling."""
    
    def __init__(self, stdin: bool = False, stdout: bool = False, 
                 global_progress=None, global_task=None, file_weight=0, 
                 file_index=0, total_files=0, **kwargs):
        self.stdin = stdin
        self.stdout = stdout
        self.kwargs = kwargs
        self.backend = None
        self.model_manager = ModelManager()
        self.global_progress = global_progress
        self.global_task = global_task
        self.file_weight = file_weight
        self.file_index = file_index
        self.total_files = total_files
    
    def process(self, input_path: str, output_path: str) -> None:
        """Process a video file or stream."""
        start_time = time.time()
        
        # Display processing start information
        if not self.stdin and not self.stdout:
            display_processing_start(input_path, output_path, "VIDEO", **self.kwargs)
        
        logger.info(f"Processing video: {input_path} -> {output_path}")
        
        if self.stdin:
            self._process_stdin_stream(output_path)
        elif self.stdout:
            self._process_stdout_stream(input_path)
        else:
            self._process_file(input_path, output_path)
        
        # Display completion information
        if not self.stdin and not self.stdout:
            end_time = time.time()
            self.kwargs['backend_used'] = self.backend.__class__.__name__ if self.backend else 'unknown'
            display_processing_complete(input_path, output_path, "VIDEO", 
                                       start_time, end_time, **self.kwargs)
    
    def _process_file(self, input_path: str, output_path: str) -> None:
        """Process a video file."""
        # Get video info
        video_info = get_video_info(input_path)
        
        # Display input video information
        display_video_info(video_info, "Input Video Information")
        
        logger.info(f"Input video: {video_info['width']}x{video_info['height']} @ {video_info['fps']:.2f}fps")
        
        # Calculate output dimensions
        scale = self.kwargs.get('scale', 4)
        out_width = video_info['width'] * scale
        out_height = video_info['height'] * scale
        
        # Display output video information
        console.print("")
        print_info("🎯 Output Resolution", f"{out_width} × {out_height}")
        print_info("📏 Upscale Factor", f"{scale}x")
        console.print("")
        
        logger.info(f"Output video: {out_width}x{out_height}")
        
        # Get backend
        self.backend = get_backend(**self.kwargs)
        
        # Display backend information
        backend_info = {
            'device': getattr(self.backend, 'device', 'CPU'),
            'cuda_available': getattr(self.backend, 'cuda_available', False),
            'gpu_name': getattr(self.backend, 'gpu_name', None)
        }
        display_backend_info(self.backend.__class__.__name__, backend_info)
        
        print_success(f"Backend initialized: {self.backend.__class__.__name__}")
        
        # Create temporary files for processing
        with tempfile.TemporaryDirectory(prefix='upscaler_') as temp_dir:
            temp_input_y4m = os.path.join(temp_dir, 'input.y4m')
            temp_output_y4m = os.path.join(temp_dir, 'output.y4m')
            
            # Process video
            with self.backend:
                self._extract_and_process(
                    input_path, temp_input_y4m, temp_output_y4m, 
                    video_info, out_width, out_height
                )
                
                # Encode final video
                self._encode_final_video(
                    temp_output_y4m, input_path, output_path, video_info
                )
    
    def _process_stdin_stream(self, output_path: str) -> None:
        """Process video from stdin."""
        # Read Y4M from stdin
        y4m_reader = Y4MReader(sys.stdin.buffer)
        header = y4m_reader.read_header()
        
        logger.info(f"Input stream: {header['width']}x{header['height']} @ {header['fps']:.2f}fps")
        
        # Calculate output dimensions
        scale = self.kwargs.get('scale', 4)
        out_width = header['width'] * scale
        out_height = header['height'] * scale
        
        # Get backend
        self.backend = get_backend(**self.kwargs)
        
        # Process stream
        with self.backend:
            with open(output_path, 'wb') as output_file:
                y4m_writer = Y4MWriter(output_file, out_width, out_height, header['fps'])
                y4m_writer.write_header()
                
                frame_count = 0
                while True:
                    frame_data = y4m_reader.read_frame()
                    if frame_data is None:
                        break
                    
                    # Convert YUV to RGB
                    frame_rgb = self._yuv420p_to_rgb(frame_data, header['width'], header['height'])
                    
                    # Upscale
                    upscaled_rgb = self.backend.upscale(frame_rgb)
                    
                    # Convert back to YUV
                    upscaled_yuv = self._rgb_to_yuv420p(upscaled_rgb)
                    
                    # Write frame
                    y4m_writer.write_frame(upscaled_yuv)
                    
                    frame_count += 1
                    if frame_count % 10 == 0:
                        logger.info(f"Processed {frame_count} frames")
                
                # Clear Windows Terminal progress indicator only if not part of batch
                if not self.global_progress:
                    set_windows_terminal_progress(0, state=0)  # Hide progress
                
                logger.info(f"Stream processing completed: {frame_count} frames")
    
    def _process_stdout_stream(self, input_path: str) -> None:
        """Process video to stdout."""
        # Get video info
        video_info = get_video_info(input_path)
        
        # Calculate output dimensions
        scale = self.kwargs.get('scale', 4)
        out_width = video_info['width'] * scale
        out_height = video_info['height'] * scale
        
        # Get backend
        self.backend = get_backend(**self.kwargs)
        
        # Process and output to stdout
        with self.backend:
            y4m_writer = Y4MWriter(sys.stdout.buffer, out_width, out_height, video_info['fps'])
            y4m_writer.write_header()
            
            # Extract frames and process
            self._extract_and_stream(input_path, y4m_writer, video_info)
    
    def _extract_and_process(self, input_path: str, temp_input: str, temp_output: str, 
                           video_info: Dict[str, Any], out_width: int, out_height: int) -> None:
        """Extract frames, process them, and create output Y4M."""
        
        # Extract to Y4M
        ffmpeg_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-f', 'yuv4mpegpipe',
            '-pix_fmt', 'yuv420p',
            '-y', temp_input
        ]
        
        logger.info("Extracting video to Y4M format...")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        
        # Process Y4M
        with open(temp_input, 'rb') as input_file:
            with open(temp_output, 'wb') as output_file:
                y4m_reader = Y4MReader(input_file)
                header = y4m_reader.read_header()
                
                y4m_writer = Y4MWriter(output_file, out_width, out_height, header['fps'])
                y4m_writer.write_header()
                
                # Setup progress tracking
                total_frames = video_info.get('nb_frames', 0)
                progress_format = self.kwargs.get('progress', 'bar')
                frame_count = 0
                start_time = time.time()
                
                if progress_format == 'bar' and total_frames > 0:
                    # Use global progress if available, otherwise create new one
                    if self.global_progress:
                        progress = self.global_progress
                        # Add sub-task for this video
                        task = progress.add_task(f"🎬 [{self.file_index}/{self.total_files}] Upscaling frames", total=total_frames)
                        use_context_manager = False
                    else:
                        progress_context = create_progress()
                        progress = progress_context.__enter__()
                        task = progress.add_task("🎬 Upscaling frames", total=total_frames)
                        use_context_manager = True
                    
                    try:
                        # Time-based refresh control (80ms intervals)
                        next_refresh_time = 0.0
                        REFRESH_INTERVAL = 0.08  # 80ms for smooth updates without flicker
                        
                        while True:
                            frame_data = y4m_reader.read_frame()
                            if frame_data is None:
                                break
                            
                            # Convert YUV to RGB
                            frame_rgb = self._yuv420p_to_rgb(frame_data, header['width'], header['height'])
                            
                            # Upscale
                            upscaled_rgb = self.backend.upscale(frame_rgb)
                            
                            # Face enhancement if requested
                            if self.kwargs.get('face_enhance', False):
                                upscaled_rgb = self._enhance_faces(upscaled_rgb)
                            
                            # Convert back to YUV
                            upscaled_yuv = self._rgb_to_yuv420p(upscaled_rgb)
                            
                            # Write frame
                            y4m_writer.write_frame(upscaled_yuv)
                            
                            frame_count += 1
                            
                            # Calculate speed
                            elapsed = time.time() - start_time
                            speed = frame_count / elapsed if elapsed > 0 else 0
                            
                            # Update progress internally (no refresh)
                            progress.update(task, advance=1, speed=speed)
                            
                            # Update global progress if available
                            if self.global_progress and self.global_task:
                                # Calculate overall progress
                                file_progress = frame_count / total_frames
                                overall_progress = (self.file_index - 1 + file_progress) * self.file_weight
                                self.global_progress.update(self.global_task, completed=overall_progress * self.total_files)
                            
                            # Time-based screen refresh
                            current_time = time.perf_counter()
                            if current_time >= next_refresh_time or frame_count == total_frames:
                                progress.refresh()  # Manual refresh
                                next_refresh_time = current_time + REFRESH_INTERVAL
                                
                                # Update Windows Terminal progress indicator
                                percent = (frame_count / total_frames) * 100
                                set_windows_terminal_progress(percent)
                    finally:
                        # Clean up context manager if we created one
                        if use_context_manager and 'progress_context' in locals():
                            progress_context.__exit__(None, None, None)
                else:
                    # No progress bar mode
                    while True:
                        frame_data = y4m_reader.read_frame()
                        if frame_data is None:
                            break
                        
                        # Convert YUV to RGB
                        frame_rgb = self._yuv420p_to_rgb(frame_data, header['width'], header['height'])
                        
                        # Upscale
                        upscaled_rgb = self.backend.upscale(frame_rgb)
                        
                        # Face enhancement if requested
                        if self.kwargs.get('face_enhance', False):
                            upscaled_rgb = self._enhance_faces(upscaled_rgb)
                        
                        # Convert back to YUV
                        upscaled_yuv = self._rgb_to_yuv420p(upscaled_rgb)
                        
                        # Write frame
                        y4m_writer.write_frame(upscaled_yuv)
                        
                        frame_count += 1
                        
                        # JSON progress update
                        if progress_format == 'json':
                            json_progress = frame_count / total_frames if total_frames > 0 else 0
                            print(f'{{"status": "processing", "progress": {json_progress:.3f}, "frame": {frame_count}}}')
                
                logger.info(f"Processed {frame_count} frames")
                
                # Clear Windows Terminal progress indicator only if not part of batch
                if not self.global_progress:
                    set_windows_terminal_progress(0, state=0)  # Hide progress
    
    def _extract_and_stream(self, input_path: str, y4m_writer: Y4MWriter, video_info: Dict[str, Any]) -> None:
        """Extract and stream frames to stdout."""
        
        # Use ffmpeg to extract frames
        ffmpeg_cmd = [
            get_ffmpeg_path(),
            '-i', input_path,
            '-f', 'rawvideo',
            '-pix_fmt', 'rgb24',
            '-'
        ]
        
        with subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE) as proc:
            frame_size = video_info['width'] * video_info['height'] * 3
            frame_count = 0
            
            while True:
                frame_data = proc.stdout.read(frame_size)
                if len(frame_data) != frame_size:
                    break
                
                # Convert to numpy array
                frame_rgb = np.frombuffer(frame_data, dtype=np.uint8).reshape(
                    (video_info['height'], video_info['width'], 3)
                )
                
                # Upscale
                upscaled_rgb = self.backend.upscale(frame_rgb)
                
                # Convert to YUV and write
                upscaled_yuv = self._rgb_to_yuv420p(upscaled_rgb)
                y4m_writer.write_frame(upscaled_yuv)
                
                frame_count += 1
                if frame_count % 10 == 0:
                    logger.info(f"Streamed {frame_count} frames")
    
    def _encode_final_video(self, temp_y4m: str, original_input: str, output_path: str, 
                          video_info: Dict[str, Any]) -> None:
        """Encode final video with audio from original."""
        
        logger.info("Encoding final video...")
        
        # Build ffmpeg command
        ffmpeg_cmd = [
            get_ffmpeg_path(),
            '-i', temp_y4m,  # Upscaled video
            '-i', original_input,  # Original for audio
            '-map', '0:v',  # Video from first input
        ]
        
        # Add audio mapping if copy_audio is enabled
        if self.kwargs.get('copy_audio', True):
            ffmpeg_cmd.extend(['-map', '1:a?'])  # Audio from second input (optional)
        
        # Video encoding settings
        ffmpeg_cmd.extend([
            '-c:v', 'libx264',
            '-crf', '18',
            '-preset', 'medium',
            '-pix_fmt', 'yuv420p'
        ])
        
        # Audio settings
        if self.kwargs.get('copy_audio', True):
            ffmpeg_cmd.extend(['-c:a', 'copy'])
        
        # Output
        ffmpeg_cmd.extend(['-y', output_path])
        
        try:
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            logger.info(f"Video encoding completed: {output_path}")
            
            # Final progress update
            if self.kwargs.get('progress') == 'json':
                print(f'{{"status": "completed", "progress": 1.0, "message": "Video processing completed"}}')
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Video encoding failed: {e.stderr}")
            raise RuntimeError(f"Video encoding failed: {e}")
    
    def _yuv420p_to_rgb(self, yuv_data: bytes, width: int, height: int) -> np.ndarray:
        """Convert YUV420P frame data to RGB numpy array."""
        
        # YUV420P layout: Y plane, then U plane (1/4 size), then V plane (1/4 size)
        y_size = width * height
        uv_size = y_size // 4
        
        y_plane = np.frombuffer(yuv_data[:y_size], dtype=np.uint8).reshape((height, width))
        u_plane = np.frombuffer(yuv_data[y_size:y_size + uv_size], dtype=np.uint8).reshape((height // 2, width // 2))
        v_plane = np.frombuffer(yuv_data[y_size + uv_size:], dtype=np.uint8).reshape((height // 2, width // 2))
        
        # Upsample U and V planes
        u_upsampled = cv2.resize(u_plane, (width, height), interpolation=cv2.INTER_LINEAR)
        v_upsampled = cv2.resize(v_plane, (width, height), interpolation=cv2.INTER_LINEAR)
        
        # Convert YUV to RGB
        yuv_image = np.stack([y_plane, u_upsampled, v_upsampled], axis=-1)
        rgb_image = cv2.cvtColor(yuv_image, cv2.COLOR_YUV2RGB)
        
        return rgb_image
    
    def _rgb_to_yuv420p(self, rgb_image: np.ndarray) -> bytes:
        """Convert RGB numpy array to YUV420P frame data."""
        
        # Convert RGB to YUV
        yuv_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2YUV)
        
        height, width = rgb_image.shape[:2]
        
        # Extract Y, U, V planes
        y_plane = yuv_image[:, :, 0]
        u_plane = yuv_image[:, :, 1]
        v_plane = yuv_image[:, :, 2]
        
        # Downsample U and V planes for 420 format
        u_downsampled = cv2.resize(u_plane, (width // 2, height // 2), interpolation=cv2.INTER_LINEAR)
        v_downsampled = cv2.resize(v_plane, (width // 2, height // 2), interpolation=cv2.INTER_LINEAR)
        
        # Concatenate planes
        yuv_data = y_plane.tobytes() + u_downsampled.tobytes() + v_downsampled.tobytes()
        
        return yuv_data
    
    def _enhance_faces(self, image: np.ndarray) -> np.ndarray:
        """Enhance faces using GFPGAN."""
        try:
            # This is a placeholder - would need actual GFPGAN implementation
            logger.warning("Face enhancement not yet implemented")
            return image
            
        except Exception as e:
            logger.warning(f"Face enhancement failed: {e}")
            return image