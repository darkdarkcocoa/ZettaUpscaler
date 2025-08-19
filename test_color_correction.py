"""Test upscaling with improved color correction"""

import sys
sys.path.insert(0, r'D:\Workspace\Upscaler')

from upscaler.processors import ImageProcessor
import os

# Test image path (use the existing image in the folder)
input_image = r"D:\Workspace\Upscaler\78c54532d117e3eb0c3e8f5598722fa6.jpg"
output_image = r"D:\Workspace\Upscaler\output_corrected.jpg"

print("Testing upscaling with color correction...")
print(f"Input: {input_image}")
print(f"Output: {output_image}")

# Create processor with improved settings
processor = ImageProcessor(
    backend='auto',
    model='realesr-general-x4v3',
    scale=4,
    gamma=0.85,  # Slightly brighter to compensate
    preserve_tone=True,  # Enable histogram matching
    tile=256,
    tile_overlap=32
)

try:
    processor.process(input_image, output_image)
    print("✅ Upscaling completed successfully!")
    print("Please check the output image for improved color tone.")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
