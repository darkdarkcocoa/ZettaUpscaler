from PIL import Image, ImageDraw, ImageFont
import os

# 테스트 이미지 생성
for i in range(3):
    img = Image.new('RGB', (200, 200), color=(255, 100, 100))
    draw = ImageDraw.Draw(img)
    
    # 텍스트 추가
    text = f"Test {i+1}"
    draw.text((50, 90), text, fill=(255, 255, 255), font=None)
    
    # 저장
    img.save(f'test_image_{i+1}.jpg')
    print(f'Created test_image_{i+1}.jpg')

print("Test images created!")