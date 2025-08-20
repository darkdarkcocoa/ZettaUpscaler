"""
Improved Real-ESRGAN wrapper with architecture detection
Based on GPT-5 and Claude consensus
"""

import torch
import numpy as np
import logging
from pathlib import Path
from .model_detector import detect_architecture

logger = logging.getLogger(__name__)


def load_realesrgan_model(model_path, device='cuda', scale=4):
    """Load Real-ESRGAN model with automatic architecture detection"""
    
    model_path = Path(model_path)
    logger.info(f"Loading model: {model_path.name}")
    
    # Detect architecture
    arch_name, arch_params, score = detect_architecture(str(model_path), device)
    
    logger.info(f"Detected architecture: {arch_name} (confidence: {score:.2%})")
    logger.debug(f"Architecture parameters: {arch_params}")
    
    # Warn if confidence is low
    if score < 0.95:
        logger.warning(f"Low confidence in architecture detection ({score:.2%})")
        logger.warning("Model may not load correctly, expect potential issues")
    
    # Build appropriate model
    if arch_name == 'RRDBNet':
        from ..archs.rrdbnet import RRDBNet
        model = RRDBNet(**arch_params)
    elif arch_name == 'SRVGGNetCompact':
        # Try official basicsr first if available
        try:
            from basicsr.archs.srvgg_arch import SRVGGNetCompact
            logger.info("Using official SRVGGNetCompact from basicsr")
        except ImportError:
            logger.warning("basicsr not available, using custom implementation")
            from ..archs.srvgg_arch_fixed import SRVGGNetCompact
        model = SRVGGNetCompact(**arch_params)
    else:
        raise ValueError(f"Unknown architecture: {arch_name}")
    
    # Load checkpoint
    checkpoint = torch.load(str(model_path), map_location='cpu')
    
    # Extract state dict (EMA priority)
    state_dict = (checkpoint.get('params_ema') or 
                  checkpoint.get('params') or 
                  checkpoint.get('state_dict') or 
                  checkpoint)
    
    # Remove module. prefix if present
    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
    
    # Load weights
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    
    # Log loading statistics
    loaded = len(model.state_dict()) - len(missing_keys)
    total = len(model.state_dict())
    load_ratio = loaded / max(1, total)
    
    logger.info(f"Model loading: {loaded}/{total} keys loaded ({load_ratio:.1%})")
    
    if missing_keys:
        logger.warning(f"Missing keys ({len(missing_keys)}): {missing_keys[:5]}...")
    if unexpected_keys:
        logger.debug(f"Unexpected keys ({len(unexpected_keys)}): {unexpected_keys[:5]}...")
    
    if load_ratio < 0.95:
        logger.error(f"INCOMPLETE MODEL LOADING! Only {loaded}/{total} keys loaded")
        logger.error("This WILL cause quality degradation or color distortion!")
    
    # Move to device and set to eval mode
    model.to(device)
    model.eval()
    
    return model


def upscale_image(model, img, device='cuda', scale=4, gamma=1.0):
    """Upscale image with FIXED memory contiguity (Gemini DeepThink solution)"""
    
    # Ensure input is BGR uint8
    if img.dtype != np.uint8:
        img = np.clip(img * 255, 0, 255).astype(np.uint8)
    
    # CRITICAL FIX: Ensure memory contiguity after transpose
    # (H, W, C) -> (C, H, W)
    img_chw = img.transpose(2, 0, 1)
    
    # !!! SOLUTION: Make array contiguous in memory !!!
    img_chw = np.ascontiguousarray(img_chw)
    
    # Convert to tensor with proper memory layout
    img_tensor = torch.from_numpy(img_chw).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0).to(device)
    
    # Inference
    with torch.no_grad():
        output = model(img_tensor)
    
    # Convert back: [0,1] -> uint8
    output = output.squeeze(0).cpu().clamp(0, 1)
    output_np = output.numpy()
    
    # (C, H, W) -> (H, W, C)
    output_hwc = output_np.transpose(1, 2, 0)
    
    # Ensure contiguity for output as well
    output_hwc = np.ascontiguousarray(output_hwc)
    
    output_result = (output_hwc * 255).astype(np.uint8)
    
    return output_result