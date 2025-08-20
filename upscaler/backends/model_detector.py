"""
Model architecture detection and caching utilities
Based on GPT-5 and Claude consensus
"""

import torch
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


def detect_architecture(model_path: str, device: str = 'cpu') -> Tuple[str, Dict[str, Any], float]:
    """
    Detect model architecture from checkpoint file
    Returns: (arch_name, arch_params, match_score)
    """
    model_path = Path(model_path)
    
    # Try cache first
    cached = load_from_cache(model_path)
    if cached:
        logger.info(f"Using cached architecture: {cached['arch_name']}")
        return cached['arch_name'], cached['arch_params'], cached['score']
    
    # Load checkpoint
    checkpoint = torch.load(str(model_path), map_location=device)
    
    # Extract state dict (EMA priority)
    state_dict = (checkpoint.get('params_ema') or 
                  checkpoint.get('params') or 
                  checkpoint.get('state_dict') or 
                  checkpoint)
    
    # Remove module. prefix if present
    state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
    
    # Check metadata first
    if 'arch_name' in checkpoint:
        arch_name = checkpoint['arch_name']
        arch_params = checkpoint.get('arch_params', {})
        score = verify_architecture(arch_name, arch_params, state_dict)
        if score >= 0.95:
            save_to_cache(model_path, arch_name, arch_params, score)
            return arch_name, arch_params, score
    
    # Filename hints
    filename = model_path.stem.lower()
    candidates = []
    
    if 'realesr-general' in filename:
        candidates.append('SRVGGNetCompact')
    elif any(x in filename for x in ['x4plus', 'animevideo', 'anime']):
        candidates.append('RRDBNet')
    
    # Pattern detection
    keys = list(state_dict.keys())
    has_rdb = any('rdb' in k for k in keys)
    has_body_weight = any(re.match(r'^body\.\d+\.weight$', k) for k in keys)
    
    if has_rdb:
        candidates.append('RRDBNet')
    if has_body_weight and not has_rdb:
        candidates.append('SRVGGNetCompact')
    
    # If no candidates, try both
    if not candidates:
        candidates = ['SRVGGNetCompact', 'RRDBNet']
    
    # Score each candidate
    best_arch = None
    best_params = {}
    best_score = 0
    
    for arch_name in candidates:
        arch_params = infer_arch_params(arch_name, state_dict)
        score = verify_architecture(arch_name, arch_params, state_dict)
        
        logger.info(f"Architecture {arch_name} score: {score:.2%}")
        
        if score > best_score:
            best_arch = arch_name
            best_params = arch_params
            best_score = score
    
    # Diagnostic logging if score is low
    if best_score < 0.95:
        logger.warning(f"Low architecture match score: {best_score:.2%} for {best_arch}")
        log_mismatch_details(best_arch, best_params, state_dict)
    
    # Save to cache
    save_to_cache(model_path, best_arch, best_params, best_score)
    
    return best_arch, best_params, best_score


def infer_arch_params(arch_name: str, state_dict: Dict) -> Dict[str, Any]:
    """Infer architecture parameters from state dict"""
    params = {}
    
    if arch_name == 'RRDBNet':
        # Get input/output channels and features
        if 'conv_first.weight' in state_dict:
            shape = state_dict['conv_first.weight'].shape
            params['num_feat'] = shape[0]
            params['num_in_ch'] = shape[1]
        
        # Count RRDB blocks
        rrdb_blocks = set()
        for key in state_dict:
            match = re.match(r'body\.(\d+)\.', key)
            if match:
                rrdb_blocks.add(int(match.group(1)))
        params['num_block'] = len(rrdb_blocks) if rrdb_blocks else 23
        
        # Get grow channels
        if 'body.0.rdb1.conv1.weight' in state_dict:
            params['num_grow_ch'] = state_dict['body.0.rdb1.conv1.weight'].shape[0]
        else:
            params['num_grow_ch'] = 32
        
        # Detect scale
        if 'upconv2.weight' in state_dict:
            params['scale'] = 4
        elif 'upconv1.weight' in state_dict:
            params['scale'] = 2
        else:
            params['scale'] = 4
        
        params['num_out_ch'] = params.get('num_in_ch', 3)
    
    elif arch_name == 'SRVGGNetCompact':
        # Get input/output channels and features
        if 'conv_first.weight' in state_dict:
            shape = state_dict['conv_first.weight'].shape
            params['num_feat'] = shape[0]
            params['num_in_ch'] = shape[1]
        
        if 'conv_last.weight' in state_dict:
            params['num_out_ch'] = state_dict['conv_last.weight'].shape[0]
        else:
            params['num_out_ch'] = 3
        
        # Count conv layers in body
        conv_count = 0
        for key in state_dict:
            if re.match(r'^body\.\d+\.weight$', key):
                conv_count += 1
        params['num_conv'] = conv_count if conv_count > 0 else 32
        
        # Detect activation type (prelu or lrelu)
        has_prelu = any('prelu' in k.lower() for k in state_dict)
        params['act_type'] = 'prelu' if has_prelu else 'lrelu'
        
        # Detect scale from upsampler
        if 'upsampler.0.weight' in state_dict:
            out_ch = state_dict['upsampler.0.weight'].shape[0]
            num_feat = params.get('num_feat', 64)
            # For 4x, we have two upsampling layers, each 2x
            # out_ch = num_feat * scale^2 for pixel shuffle
            scale_sq = out_ch // num_feat
            params['upscale'] = int(scale_sq ** 0.5) if scale_sq in [4, 16] else 4
        else:
            params['upscale'] = 4
    
    return params


def verify_architecture(arch_name: str, arch_params: Dict, state_dict: Dict) -> float:
    """Verify if architecture matches state dict and return match score"""
    
    # Build model to get expected keys
    if arch_name == 'RRDBNet':
        from ..archs.rrdbnet import RRDBNet
        model = RRDBNet(**arch_params)
    elif arch_name == 'SRVGGNetCompact':
        # Try official basicsr first if available
        try:
            from basicsr.archs.srvgg_arch import SRVGGNetCompact
            logger.info("Using official SRVGGNetCompact from basicsr")
        except ImportError:
            from ..archs.srvgg_arch_fixed import SRVGGNetCompact
            logger.info("Using custom SRVGGNetCompact implementation")
        model = SRVGGNetCompact(**arch_params)
    else:
        return 0.0
    
    model_state = model.state_dict()
    
    # Calculate match score
    matched_keys = 0
    total_keys = len(model_state)
    
    for key, param in model_state.items():
        if key in state_dict:
            if state_dict[key].shape == param.shape:
                matched_keys += 1
    
    score = matched_keys / max(1, total_keys)
    return score


def log_mismatch_details(arch_name: str, arch_params: Dict, state_dict: Dict):
    """Log detailed mismatch information for debugging"""
    
    # Build model to compare
    if arch_name == 'RRDBNet':
        from ..archs.rrdbnet import RRDBNet
        model = RRDBNet(**arch_params)
    elif arch_name == 'SRVGGNetCompact':
        # Try official basicsr first if available
        try:
            from basicsr.archs.srvgg_arch import SRVGGNetCompact
            logger.info("Using official SRVGGNetCompact from basicsr")
        except ImportError:
            from ..archs.srvgg_arch_fixed import SRVGGNetCompact
            logger.info("Using custom SRVGGNetCompact implementation")
        model = SRVGGNetCompact(**arch_params)
    else:
        return
    
    model_state = model.state_dict()
    
    # Find missing and mismatched keys
    missing_keys = []
    shape_mismatches = []
    unexpected_keys = []
    
    for key, param in model_state.items():
        if key not in state_dict:
            missing_keys.append(key)
        elif state_dict[key].shape != param.shape:
            shape_mismatches.append(f"{key}: expected {param.shape}, got {state_dict[key].shape}")
    
    for key in state_dict:
        if key not in model_state:
            unexpected_keys.append(key)
    
    # Log details
    logger.error(f"Architecture mismatch details for {arch_name}:")
    logger.error(f"  Parameters: {arch_params}")
    logger.error(f"  Missing keys ({len(missing_keys)}): {missing_keys[:5]}...")
    logger.error(f"  Shape mismatches ({len(shape_mismatches)}): {shape_mismatches[:5]}...")
    logger.error(f"  Unexpected keys ({len(unexpected_keys)}): {unexpected_keys[:5]}...")


def load_from_cache(model_path: Path) -> Optional[Dict]:
    """Load cached architecture detection result"""
    cache_file = model_path.parent / '.arch_cache.json'
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        
        # Verify cache validity
        model_key = str(model_path.absolute())
        if model_key not in cache:
            return None
        
        entry = cache[model_key]
        
        # Check file modification time
        current_mtime = model_path.stat().st_mtime
        if entry.get('mtime') != current_mtime:
            logger.info("Model file modified, cache invalidated")
            return None
        
        return entry
        
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def save_to_cache(model_path: Path, arch_name: str, arch_params: Dict, score: float):
    """Save architecture detection result to cache"""
    cache_file = model_path.parent / '.arch_cache.json'
    model_key = str(model_path.absolute())
    
    # Load existing cache or create new
    cache = {}
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            cache = {}
    
    # Update cache entry
    cache[model_key] = {
        'arch_name': arch_name,
        'arch_params': arch_params,
        'score': score,
        'mtime': model_path.stat().st_mtime,
        'size': model_path.stat().st_size,
        'timestamp': datetime.now().isoformat(),
        'schema_version': '1.0'
    }
    
    # Save cache
    try:
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        logger.debug(f"Saved architecture cache: {arch_name} (score: {score:.2%})")
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")