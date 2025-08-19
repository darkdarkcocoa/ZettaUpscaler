# 🚀 ZettaUpscaler

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![CUDA](https://img.shields.io/badge/CUDA-12.1-green.svg)](https://developer.nvidia.com/cuda-toolkit)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A high-performance AI-powered video and image upscaling tool using Real-ESRGAN. Supports GPU acceleration with NVIDIA GPUs for real-time upscaling up to 4x resolution.

## ✨ Features

- 🎨 **AI-Powered Upscaling**: Uses Real-ESRGAN models for high-quality upscaling
- 🎮 **GPU Acceleration**: Automatic NVIDIA GPU detection and optimization
- 📹 **Video Support**: Process entire videos with audio preservation
- 🖼️ **Batch Processing**: Handle multiple images efficiently
- 🔧 **Multiple Models**: Choose from different models for photos, anime, or general content
- 💻 **Cross-Platform**: Works on Windows, with CPU fallback for non-NVIDIA systems

## 📸 Examples

| Original (736×1104) | 4x Upscaled (2944×4416) |
|---------------------|-------------------------|
| ![Original](docs/original.jpg) | ![Upscaled](docs/upscaled.jpg) |

## 🚀 Quick Start

### For Users (Windows EXE)

1. Download the latest release from [Releases](https://github.com/darkdarkcocoa/ZettaUpscaler/releases)
2. Extract the ZIP file
3. Run the upscaler:
```bash
upscaler.exe image input.jpg output.jpg --scale 4
upscaler.exe video input.mp4 output.mp4 --scale 4 --copy-audio
```

### For Developers

#### Prerequisites
- Python 3.12
- NVIDIA GPU with CUDA 12.1 support (optional, for GPU acceleration)
- FFmpeg (for video processing)

#### Installation

1. Clone the repository:
```bash
git clone https://github.com/darkdarkcocoa/ZettaUpscaler.git
cd ZettaUpscaler
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
# For GPU support (NVIDIA)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# For CPU only
pip install torch torchvision
pip install -r requirements.txt
```

4. Fix compatibility issues (if needed):
```bash
python fix_compatibility.py
```

5. Run the upscaler:
```bash
python -m upscaler image input.jpg output.jpg --scale 4
python -m upscaler video input.mp4 output.mp4 --scale 4
```

## 📖 Usage

### Command Line Interface

```bash
# Basic image upscaling
upscaler image input.jpg output.jpg --scale 4

# Video upscaling with audio
upscaler video input.mp4 output.mp4 --scale 4 --copy-audio

# Use specific model
upscaler image anime.jpg anime_4x.jpg --model realesrgan-x4plus-anime

# Advanced options
upscaler image photo.jpg photo_4x.jpg \
    --scale 4 \
    --model realesrgan-x4plus \
    --tile 256 \
    --fp16 \
    --face-enhance
```

### Available Models

| Model | Best For | Scale |
|-------|----------|-------|
| `realesr-general-x4v3` | General purpose (default) | 4x |
| `realesrgan-x4plus` | Photographs | 4x |
| `realesrgan-x4plus-anime` | Anime/illustrations | 4x |
| `gfpgan-1.4` | Face enhancement | 1x |

### Options

- `--scale`: Upscaling factor (2 or 4, default: 4)
- `--model`: Model to use for upscaling
- `--tile`: Tile size for processing (0 for auto)
- `--tile-overlap`: Tile overlap in pixels (default: 32)
- `--face-enhance`: Enable face enhancement with GFPGAN
- `--fp16`: Use half precision for lower VRAM usage
- `--backend`: Force specific backend (auto/torch/ncnn)
- `--copy-audio`: Copy audio from input video (default: true)

## 🛠️ Building from Source

### Build Executable (Windows)

```bash
# Install PyInstaller
pip install pyinstaller

# Build release version
build-release.bat

# Output will be in: releases/upscaler-1.0.0-win64.zip
```

## 🎮 GPU Compatibility

| GPU Series | Support | Performance |
|------------|---------|-------------|
| RTX 40 Series (4090, 4080, 4070, 4060) | ✅ Excellent | Fastest |
| RTX 30 Series (3090, 3080, 3070, 3060) | ✅ Excellent | Fast |
| RTX 20 Series (2080 Ti, 2070, 2060) | ✅ Good | Fast |
| GTX 16 Series (1660, 1650) | ✅ Good | Moderate |
| GTX 10 Series (1080 Ti, 1070, 1060) | ⚠️ Limited | Slow |
| AMD Radeon | ❌ CPU Only | Very Slow |
| Intel Arc/Iris | ❌ CPU Only | Very Slow |

## 📊 Performance

Performance on RTX 4060 Ti (1080p → 4K upscaling):
- Image (1920×1080): ~5-7 seconds
- Video (1080p, 1 minute): ~3-5 minutes

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) - Core upscaling models
- [GFPGAN](https://github.com/TencentARC/GFPGAN) - Face enhancement
- [BasicSR](https://github.com/XPixelGroup/BasicSR) - Super-resolution framework
- [PyTorch](https://pytorch.org/) - Deep learning framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/darkdarkcocoa/ZettaUpscaler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/darkdarkcocoa/ZettaUpscaler/discussions)

## ⚠️ Disclaimer

This tool uses AI models that require significant computational resources. GPU acceleration is highly recommended for practical use. Processing times on CPU-only systems may be very long.

---

Made with ❤️ by [darkdarkcocoa](https://github.com/darkdarkcocoa)