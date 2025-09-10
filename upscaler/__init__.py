"""
Video Upscaling CLI Tool
A high-performance video upscaling tool using Real-ESRGAN and other models.
"""
import os
import logging

# Suppress verbose output from RealESRGAN (Tile X/Y messages)
os.environ['REALESRGAN_VERBOSE'] = '0'
logging.getLogger('basicsr').setLevel(logging.WARNING)
logging.getLogger('realesrgan').setLevel(logging.WARNING)

__version__ = "0.1.0"
__author__ = "AI Assistant"