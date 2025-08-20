# Real-ESRGAN Color Distortion Problem Analysis

## Problem Description
- **Original**: Natural colors (gray cardigan, natural skin tone, black skirt)
- **Result**: Severe color distortion (pink/blue tint, wrong channel colors)
- **Issue**: Both image and video upscaling produce incorrect colors

## What We've Tried
1. **Gamma correction fixes**:
   - Fixed gamma value inconsistency (CLI: 0.9 vs Backend: 1.7 → unified to 1.0)
   - Removed duplicate gamma processing

2. **Color pipeline simplification**:
   - Removed sRGB ↔ linear conversions (following GPT-5 advice)
   - Simplified to direct BGR uint8 pipeline

3. **Channel order experiments**:
   - Tried BGR input → RGB model → BGR output
   - Tried RGB input → RGB model → BGR output  
   - Various combinations with cv2.cvtColor conversions

## Current Status
- **Processing works**: Images upscale successfully, resolution increases 4x
- **Color fails**: Consistent color distortion regardless of approach
- **Pattern**: Pink/blue tints suggest Red/Blue channel swapping

## Suspected Root Causes
1. Model file corruption or wrong model format
2. Real-ESRGAN implementation incompatibility
3. Fundamental misunderstanding of expected input/output format
4. Hidden color space conversions in the pipeline

## Key Files to Analyze
1. `1_cli.py` - Entry point and parameter handling
2. `2_image_processor.py` - Main image processing pipeline  
3. `3_torch_backend.py` - PyTorch backend implementation
4. `4_realesrgan_wrapper.py` - Core Real-ESRGAN inference logic
5. `5_backends_init.py` - Backend selection logic
6. `6_color_correction.py` - Color utilities (may be causing issues)
7. `7_video_processor.py` - Video processing (shows YUV conversion)
8. `8_original_input.png` - Test image for reference

## Technical Environment
- Python CLI tool using PyTorch + Real-ESRGAN
- Model: realesr-general-x4v3
- Backend: TorchBackend (CUDA not available, CPU mode)
- Input: 585x868 PNG → Output: 2340x3472 PNG