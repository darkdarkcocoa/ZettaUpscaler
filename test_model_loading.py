#!/usr/bin/env python
"""Test script to verify model loading works correctly"""

import logging
from upscaler.backends.torch_backend import TorchBackend
from upscaler.models import ModelManager

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_model_loading():
    print("Testing model loading with new implementation...")
    
    # Create backend
    backend = TorchBackend(device='cpu', model='realesr-general-x4v3')
    
    # Initialize (this will load the model)
    try:
        backend.initialize()
        print("✅ Model loaded successfully!")
        
        # Check model type
        if backend.model_instance is not None:
            print(f"Model type: {type(backend.model_instance).__name__}")
            print(f"Model class: {backend.model_instance.__class__}")
            
            # Check if it's SRVGGNetCompact (should be for realesr-general-x4v3)
            if 'SRVGG' in str(type(backend.model_instance)):
                print("✅ Correctly loaded as SRVGGNetCompact!")
            elif 'RRDB' in str(type(backend.model_instance)):
                print("⚠️ Loaded as RRDBNet (incorrect for this model)")
            else:
                print(f"❓ Unknown model type: {type(backend.model_instance)}")
                
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        backend.cleanup()

if __name__ == "__main__":
    test_model_loading()