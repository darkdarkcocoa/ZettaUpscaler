"""Color correction utilities for proper sRGB handling"""

import numpy as np
import cv2


def srgb_to_linear(img):
    """Convert sRGB to linear RGB (proper gamma correction)"""
    img_float = img.astype(np.float32) / 255.0
    
    # Apply sRGB to linear transformation
    # Values <= 0.04045 are linear, values > 0.04045 use gamma 2.4
    linear = np.where(
        img_float <= 0.04045,
        img_float / 12.92,
        np.power((img_float + 0.055) / 1.055, 2.4)
    )
    return linear


def linear_to_srgb(img):
    """Convert linear RGB to sRGB (inverse gamma correction)"""
    # Apply linear to sRGB transformation
    srgb = np.where(
        img <= 0.0031308,
        img * 12.92,
        1.055 * np.power(img, 1.0/2.4) - 0.055
    )
    
    # Clip and convert to uint8
    srgb = np.clip(srgb * 255.0, 0, 255)
    return srgb.round().astype(np.uint8)


def match_histogram(source, reference):
    """Match histogram of source image to reference image"""
    
    matched = np.zeros_like(source)
    
    for i in range(3):  # Process each color channel
        # Calculate histograms
        hist_src, _ = np.histogram(source[:,:,i].flatten(), 256, [0,256])
        hist_ref, _ = np.histogram(reference[:,:,i].flatten(), 256, [0,256])
        
        # Calculate CDFs
        cdf_src = hist_src.cumsum()
        cdf_ref = hist_ref.cumsum()
        
        # Normalize CDFs
        cdf_src = cdf_src / cdf_src[-1]
        cdf_ref = cdf_ref / cdf_ref[-1]
        
        # Create mapping
        mapping = np.zeros(256, dtype=np.uint8)
        for j in range(256):
            idx = np.searchsorted(cdf_ref, cdf_src[j])
            mapping[j] = min(idx, 255)
        
        # Apply mapping
        matched[:,:,i] = mapping[source[:,:,i]]
    
    return matched


def auto_color_balance(img, percentile=1):
    """Auto color balance using percentile clipping"""
    balanced = np.zeros_like(img)
    
    for i in range(3):
        channel = img[:,:,i]
        low = np.percentile(channel, percentile)
        high = np.percentile(channel, 100 - percentile)
        
        # Stretch histogram
        stretched = np.clip((channel - low) * 255.0 / (high - low), 0, 255)
        balanced[:,:,i] = stretched.astype(np.uint8)
    
    return balanced
