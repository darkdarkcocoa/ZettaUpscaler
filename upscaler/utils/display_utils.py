"""
Display utilities for showing processing information.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from colorama import init, Fore, Style, Back
import humanize

# Initialize colorama for Windows with UTF-8 support
init(autoreset=True)
# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    return humanize.naturalsize(size_bytes, binary=True)

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed file information."""
    path = Path(file_path)
    if not path.exists():
        return {}
    
    stat = path.stat()
    return {
        'name': path.name,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': path.suffix.lower()
    }

def print_separator(char='=', length=80):
    """Print a separator line."""
    print(Fore.CYAN + char * length)

def print_header(title: str):
    """Print a styled header."""
    print_separator('=')
    print(Fore.YELLOW + Style.BRIGHT + f"  {title.upper()}")
    print_separator('=')

def print_info(label: str, value: str, indent: int = 2):
    """Print labeled information."""
    padding = ' ' * indent
    print(f"{padding}{Fore.CYAN}{label:.<30} {Fore.WHITE}{value}")

def print_success(message: str):
    """Print success message."""
    print(f"{Fore.GREEN}[SUCCESS] {message}")

def print_warning(message: str):
    """Print warning message."""
    print(f"{Fore.YELLOW}[WARNING] {message}")

def print_error(message: str):
    """Print error message."""
    print(f"{Fore.RED}[ERROR] {message}")

def display_processing_start(input_path: str, output_path: str, mode: str, **kwargs):
    """Display processing start information."""
    print()
    print_header(f"{mode} UPSCALING STARTED")
    
    # Input file info
    input_info = get_file_info(input_path)
    if input_info:
        print(Fore.WHITE + "\n[INPUT FILE INFO]")
        print_info("File Name", input_info['name'])
        print_info("File Size", input_info['size_formatted'])
        print_info("Modified", input_info['modified'])
    
    # Output path
    print(Fore.WHITE + "\n[OUTPUT SETTINGS]")
    print_info("Output Path", output_path)
    
    # Processing settings
    print(Fore.WHITE + "\n[PROCESSING SETTINGS]")
    print_info("Backend", kwargs.get('backend', 'auto'))
    print_info("Model", kwargs.get('model', 'realesr-general-x4v3'))
    print_info("Scale", f"{kwargs.get('scale', 4)}x")
    
    if kwargs.get('tile', 0) > 0:
        print_info("Tile Size", f"{kwargs['tile']}px")
    else:
        print_info("Tile Size", "Auto")
    
    print_info("Tile Overlap", f"{kwargs.get('tile_overlap', 32)}px")
    
    if kwargs.get('face_enhance', False):
        print_info("Face Enhancement", f"Enabled (Strength: {kwargs.get('face_strength', 1.0)})")
    
    if kwargs.get('fp16', False):
        print_info("Half Precision (FP16)", "Enabled")
    
    if kwargs.get('preserve_tone', True):
        print_info("Color Tone Preservation", "Enabled")
    
    print_separator('-')

def display_video_info(video_info: Dict[str, Any], label: str = "Video Information"):
    """Display video information."""
    print(Fore.WHITE + f"\n[{label.upper()}]")
    print_info("Resolution", f"{video_info['width']} x {video_info['height']}")
    print_info("Frame Rate", f"{video_info['fps']:.2f} fps")
    print_info("Total Frames", f"{video_info.get('total_frames', 'N/A')}")
    
    if video_info.get('duration'):
        duration_sec = video_info['duration']
        hours = int(duration_sec // 3600)
        minutes = int((duration_sec % 3600) // 60)
        seconds = int(duration_sec % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        print_info("Duration", duration_str)
    
    if video_info.get('codec'):
        print_info("Codec", video_info['codec'])
    
    if video_info.get('bitrate'):
        bitrate_mbps = video_info['bitrate'] / 1_000_000
        print_info("Bitrate", f"{bitrate_mbps:.2f} Mbps")

def display_processing_complete(input_path: str, output_path: str, mode: str, 
                               start_time: float, end_time: float, **kwargs):
    """Display processing completion information."""
    print()
    print_header(f"{mode} UPSCALING COMPLETED")
    
    # Processing time
    elapsed = end_time - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    print(Fore.WHITE + "\n[PROCESSING TIME]")
    print_info("Elapsed Time", time_str)
    
    # Input file info
    input_info = get_file_info(input_path)
    output_info = get_file_info(output_path)
    
    if input_info and output_info:
        print(Fore.WHITE + "\n[FILE COMPARISON]")
        print_info("Original Size", input_info['size_formatted'])
        print_info("Output Size", output_info['size_formatted'])
        size_ratio = output_info['size'] / input_info['size']
        print_info("Size Ratio", f"{size_ratio:.2f}x")
    
    # Summary
    print(Fore.WHITE + "\n[PROCESSING SUMMARY]")
    print_info("Model Used", kwargs.get('model', 'realesr-general-x4v3'))
    print_info("Upscale Factor", f"{kwargs.get('scale', 4)}x")
    print_info("Backend Used", kwargs.get('backend_used', kwargs.get('backend', 'auto')))
    
    if kwargs.get('face_enhance', False):
        print_info("Face Enhancement", "Applied")
    
    if kwargs.get('preserve_tone', True):
        print_info("Color Tone Preservation", "Applied")
    
    # Output location
    print(Fore.WHITE + "\n[OUTPUT FILE]")
    print(f"  {Fore.GREEN}{Style.BRIGHT}{output_path}")
    
    print_separator('=')
    print_success(f"{mode} upscaling completed successfully!")
    print()

def display_backend_info(backend_name: str, backend_info: Dict[str, Any]):
    """Display backend information."""
    print(Fore.WHITE + "\n[BACKEND INFO]")
    print_info("Backend", backend_name)
    
    if backend_info.get('device'):
        print_info("Device", backend_info['device'])
    
    if backend_info.get('gpu_name'):
        print_info("GPU", backend_info['gpu_name'])
    
    if backend_info.get('cuda_available') is not None:
        cuda_status = "Available" if backend_info['cuda_available'] else "Not Available"
        print_info("CUDA", cuda_status)
    
    if backend_info.get('memory_allocated'):
        mem_gb = backend_info['memory_allocated'] / (1024**3)
        print_info("Allocated Memory", f"{mem_gb:.2f} GB")
