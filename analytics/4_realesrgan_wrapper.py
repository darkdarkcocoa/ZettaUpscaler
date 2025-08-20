"""
Wrapper for Real-ESRGAN inference without basicsr dependency
Using direct model loading approach
"""

import torch
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_realesrgan_model(model_path, device='cuda', scale=4):
    """Load Real-ESRGAN model directly"""
    
    # Load checkpoint
    checkpoint = torch.load(model_path, map_location='cpu')
    
    # Handle different checkpoint formats
    if 'params_ema' in checkpoint:
        state_dict = checkpoint['params_ema']
    elif 'params' in checkpoint:
        state_dict = checkpoint['params']
    else:
        state_dict = checkpoint
    
    # Import or define architecture based on model
    if 'realesr-general' in str(model_path).lower():
        # This is likely SRVGGNetCompact
        from ..archs.srvgg_arch import SRVGGNetCompact
        model = SRVGGNetCompact(
            num_in_ch=3,
            num_out_ch=3, 
            num_feat=64,
            num_conv=32,
            upscale=scale,
            act_type='prelu'
        )
    else:
        # Default to RRDBNet
        from ..archs.rrdbnet import RRDBNet
        model = RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=scale
        )
    
    # Load weights - try to match keys
    model_state_dict = model.state_dict()
    filtered_state_dict = {}
    
    for k, v in state_dict.items():
        if k in model_state_dict and v.shape == model_state_dict[k].shape:
            filtered_state_dict[k] = v
        else:
            # Try without module prefix
            k_no_module = k.replace('module.', '')
            if k_no_module in model_state_dict and v.shape == model_state_dict[k_no_module].shape:
                filtered_state_dict[k_no_module] = v
    
    model.load_state_dict(filtered_state_dict, strict=False)
    model.to(device)
    model.eval()
    
    return model


def upscale_image(model, img, device='cuda', scale=4, gamma=1.0):
    """Upscale image using simple BGR uint8 pipeline (GPT-5 recommended)"""
    
    # GPT-5 advice: Real-ESRGAN expects BGR uint8 sRGB input
    # No linear conversion, no complex gamma handling - keep it simple!
    
    # Ensure input is BGR uint8
    if img.dtype != np.uint8:
        img = np.clip(img * 255, 0, 255).astype(np.uint8)
    
    # Keep original channel order - maybe the issue is elsewhere
    # Let's try without channel conversion first
    img_for_model = img.copy()
    
    # Simple normalization: uint8 -> [0,1] float32
    img_tensor = torch.from_numpy(img_for_model.transpose(2, 0, 1)).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0).to(device)
    
    # Inference
    with torch.no_grad():
        output = model(img_tensor)
    
    # Convert back: [0,1] -> uint8
    output = output.squeeze(0).cpu().clamp(0, 1)
    output_np = output.numpy().transpose(1, 2, 0)
    output_result = (output_np * 255).astype(np.uint8)
    
    return output_result