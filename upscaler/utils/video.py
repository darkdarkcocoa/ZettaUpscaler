import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import shutil


logger = logging.getLogger(__name__)


def get_video_info(video_path: Union[str, Path]) -> Dict[str, Any]:
    """Get video information using ffprobe."""
    
    ffprobe_path = shutil.which('ffprobe')
    if not ffprobe_path:
        raise RuntimeError("ffprobe not found. Please install FFmpeg.")
    
    cmd = [
        ffprobe_path,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        str(video_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract video stream info
        video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
        if not video_streams:
            raise ValueError("No video stream found")
        
        video_stream = video_streams[0]
        format_info = data.get('format', {})
        
        info = {
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'fps': eval(video_stream.get('r_frame_rate', '0/1')),  # Convert fraction to float
            'duration': float(format_info.get('duration', 0)),
            'codec': video_stream.get('codec_name', 'unknown'),
            'pixel_format': video_stream.get('pix_fmt', 'unknown'),
            'bitrate': int(format_info.get('bit_rate', 0)),
            'nb_frames': int(video_stream.get('nb_frames', 0)),
        }
        
        # Calculate nb_frames if not available
        if info['nb_frames'] == 0 and info['duration'] > 0 and info['fps'] > 0:
            info['nb_frames'] = int(info['duration'] * info['fps'])
        
        return info
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get video info: {e.stderr}")
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise RuntimeError(f"Failed to parse video info: {e}")


def validate_input(input_path: Union[str, Path]) -> bool:
    """Validate input file or stream."""
    
    if input_path == '-':
        # stdin input
        return True
    
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not path.is_file():
        raise ValueError(f"Input is not a file: {input_path}")
    
    # Check if it's a video file by trying to get info
    try:
        info = get_video_info(path)
        if info['width'] <= 0 or info['height'] <= 0:
            raise ValueError(f"Invalid video dimensions: {info['width']}x{info['height']}")
        return True
    except Exception as e:
        raise ValueError(f"Invalid video file: {e}")


def get_ffmpeg_path() -> str:
    """Get ffmpeg binary path."""
    ffmpeg_path = shutil.which('ffmpeg')
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found. Please install FFmpeg.")
    return ffmpeg_path


def get_ffprobe_path() -> str:
    """Get ffprobe binary path."""
    ffprobe_path = shutil.which('ffprobe')
    if not ffprobe_path:
        raise RuntimeError("ffprobe not found. Please install FFmpeg.")
    return ffprobe_path


class Y4MReader:
    """Reader for yuv4mpeg streams."""
    
    def __init__(self, stream):
        self.stream = stream
        self.header = None
        self.width = None
        self.height = None
        self.fps = None
        self.frame_size = None
        
    def read_header(self) -> Dict[str, Any]:
        """Read Y4M header."""
        header_line = self.stream.readline()
        if not header_line.startswith(b'YUV4MPEG2'):
            raise ValueError("Invalid Y4M stream")
        
        # Parse header parameters
        params = header_line.decode('ascii').strip().split()
        self.header = {}
        
        for param in params[1:]:  # Skip YUV4MPEG2
            if param.startswith('W'):
                self.width = int(param[1:])
                self.header['width'] = self.width
            elif param.startswith('H'):
                self.height = int(param[1:])
                self.header['height'] = self.height
            elif param.startswith('F'):
                # Frame rate (e.g., F30000:1001 for 29.97 fps)
                fps_str = param[1:]
                if ':' in fps_str:
                    num, den = fps_str.split(':')
                    self.fps = int(num) / int(den)
                else:
                    self.fps = int(fps_str)
                self.header['fps'] = self.fps
            elif param.startswith('C'):
                self.header['chroma'] = param[1:]
        
        # Calculate frame size for YUV420P
        if self.width and self.height:
            self.frame_size = self.width * self.height * 3 // 2
        
        return self.header
    
    def read_frame(self) -> Optional[bytes]:
        """Read a frame from Y4M stream."""
        if not self.header:
            raise RuntimeError("Header not read")
        
        # Read frame header
        frame_header = self.stream.readline()
        if not frame_header.startswith(b'FRAME'):
            return None
        
        # Read frame data
        frame_data = self.stream.read(self.frame_size)
        if len(frame_data) != self.frame_size:
            return None
        
        return frame_data


class Y4MWriter:
    """Writer for yuv4mpeg streams."""
    
    def __init__(self, stream, width: int, height: int, fps: float, chroma: str = '420'):
        self.stream = stream
        self.width = width
        self.height = height
        self.fps = fps
        self.chroma = chroma
        self._header_written = False
    
    def write_header(self):
        """Write Y4M header."""
        if self._header_written:
            return
        
        # Convert fps to fraction if needed
        if self.fps == int(self.fps):
            fps_str = f"{int(self.fps)}:1"
        else:
            # Simple fraction conversion
            fps_str = f"{int(self.fps * 1001)}:1001"
        
        header = f"YUV4MPEG2 W{self.width} H{self.height} F{fps_str} Ip C{self.chroma}\n"
        self.stream.write(header.encode('ascii'))
        self._header_written = True
    
    def write_frame(self, frame_data: bytes):
        """Write a frame to Y4M stream."""
        if not self._header_written:
            self.write_header()
        
        self.stream.write(b'FRAME\n')
        self.stream.write(frame_data)