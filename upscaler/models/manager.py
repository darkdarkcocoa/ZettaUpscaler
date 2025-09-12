"""
Model management system for Real-ESRGAN models
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional
import urllib.request
import urllib.error

import gdown
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model downloads and paths."""
    
    # Model definitions with download URLs and checksums
    models = {
        'realesr-general-x4v3': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
            'sha256': 'dd7de8a97048fa2d0e05aea1b5a2c83a2e3861a08c5f0c0c2821787c85cf5947',
            'scale': 4,
            'description': 'General purpose Real-ESRGAN model (SRVGGNet)'
        },
        'realesrgan-x4plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
            'sha256': '4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1',
            'scale': 4,
            'description': 'RealESRGAN x4 plus model for photorealistic images'
        },
        'realesrgan-x4plus-anime': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth',
            'sha256': 'f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da',
            'scale': 4,
            'description': 'RealESRGAN x4 plus anime optimization model'
        },
        'realesnet-x4plus': {
            'url': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.1/RealESRNet_x4plus.pth',
            'sha256': 'df35f2bff19ca942eef14a8f291e29e3b0e5a5db436f58e451968a69ad995b5c',
            'scale': 4,
            'description': 'RealESRNet x4 plus model (MSE optimization)'
        }
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize model manager."""
        if cache_dir is None:
            # Default cache directory
            if sys.platform == 'win32':
                cache_dir = os.path.expanduser('~/.cache/upscaler/models')
            else:
                cache_dir = os.path.expanduser('~/.cache/upscaler/models')
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Model cache directory: {self.cache_dir}")
    
    def get_model_path(self, model_name: str) -> Path:
        """Get the path to a model file."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}. Available models: {list(self.models.keys())}")
        
        # Check custom path first
        custom_path = os.environ.get('UPSCALER_MODEL_PATH')
        if custom_path:
            model_file = Path(custom_path) / f"{model_name}.pth"
            if model_file.exists():
                logger.info(f"Using custom model path: {model_file}")
                return model_file
        
        # Default cache path
        return self.cache_dir / f"{model_name}.pth"
    
    def is_model_downloaded(self, model_name: str) -> bool:
        """Check if a model is already downloaded."""
        model_path = self.get_model_path(model_name)
        if not model_path.exists():
            return False
        
        # Verify checksum
        model_info = self.models.get(model_name, {})
        expected_sha256 = model_info.get('sha256')
        
        if expected_sha256:
            actual_sha256 = self._calculate_sha256(model_path)
            if actual_sha256 != expected_sha256:
                logger.warning(f"Model {model_name} checksum mismatch. Re-downloading...")
                model_path.unlink()  # Remove corrupted file
                return False
        
        return True
    
    def download_model(self, model_name: str, force: bool = False) -> Path:
        """Download a model if not already present."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_path = self.get_model_path(model_name)
        
        # Check if already downloaded
        if not force and self.is_model_downloaded(model_name):
            logger.info(f"Model {model_name} already downloaded at {model_path}")
            return model_path
        
        # Download the model
        model_info = self.models[model_name]
        url = model_info['url']
        
        logger.info(f"Downloading {model_name} from {url}")
        logger.info(f"This may take a while depending on your internet connection...")
        
        # Create temporary file
        temp_path = model_path.with_suffix('.tmp')
        
        try:
            if 'drive.google.com' in url or 'docs.google.com' in url:
                # Use gdown for Google Drive
                gdown.download(url, str(temp_path), quiet=False)
            else:
                # Use urllib for GitHub releases
                self._download_with_progress(url, temp_path)
            
            # Verify checksum
            expected_sha256 = model_info.get('sha256')
            if expected_sha256:
                actual_sha256 = self._calculate_sha256(temp_path)
                if actual_sha256 != expected_sha256:
                    temp_path.unlink()
                    raise ValueError(f"Checksum mismatch for {model_name}")
                logger.info("Checksum verified ✓")
            
            # Move to final location
            temp_path.rename(model_path)
            logger.info(f"Model saved to {model_path}")
            
            return model_path
            
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to download {model_name}: {e}")
    
    def _download_with_progress(self, url: str, dest_path: Path):
        """Download a file with progress bar."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            with open(dest_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        pbar.update(len(chunk))
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def list_models(self) -> Dict[str, Dict]:
        """List all available models with their info."""
        result = {}
        for name, info in self.models.items():
            model_info = info.copy()
            model_info['downloaded'] = self.is_model_downloaded(name)
            if model_info['downloaded']:
                model_info['path'] = str(self.get_model_path(name))
                model_info['size_mb'] = self.get_model_path(name).stat().st_size / (1024 * 1024)
            result[name] = model_info
        return result
    
    def clean_cache(self):
        """Remove all downloaded models."""
        count = 0
        for model_file in self.cache_dir.glob("*.pth"):
            model_file.unlink()
            count += 1
        logger.info(f"Removed {count} model files from cache")