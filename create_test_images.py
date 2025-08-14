from PIL import Image
import os

# Create test images directory
os.makedirs('test_images', exist_ok=True)

# Create 3 test images with different colors
colors = [
    ('red', (255, 100, 100)),
    ('green', (100, 255, 100)),
    ('blue', (100, 100, 255))
]

for name, color in colors:
    img = Image.new('RGB', (800, 600), color)
    img.save(f'test_images/test_{name}.jpg', 'JPEG')
    print(f"Created test_{name}.jpg")

print("Test images created successfully in test_images/ directory")