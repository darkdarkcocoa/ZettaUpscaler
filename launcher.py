"""
Lightweight launcher for upscaler - downloads models on first run
"""
import os
import sys
import subprocess
import urllib.request
import zipfile
from pathlib import Path

MODEL_URLS = {
    'realesr-general-x4v3': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth',
    'realesrgan-x4plus': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth',
    'realesrgan-x4plus-anime': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth',
}

def download_model(model_name, model_dir):
    """Download model if not exists"""
    model_path = model_dir / f"{model_name}.pth"
    if not model_path.exists():
        print(f"Downloading {model_name} model...")
        url = MODEL_URLS.get(model_name)
        if url:
            urllib.request.urlretrieve(url, model_path)
            print(f"Downloaded {model_name}")
    return model_path

def setup_models():
    """Setup required models"""
    app_dir = Path.home() / '.upscaler'
    model_dir = app_dir / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Download default model
    download_model('realesr-general-x4v3', model_dir)
    
    return model_dir

def main():
    """Main launcher"""
    # Setup models on first run
    model_dir = setup_models()
    os.environ['UPSCALER_MODEL_DIR'] = str(model_dir)
    
    # Import and run the actual upscaler
    from upscaler.cli import cli
    cli()

if __name__ == '__main__':
    main()
