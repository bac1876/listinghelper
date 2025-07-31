"""
Create test images for virtual tour testing
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create test_images directory if it doesn't exist
os.makedirs('test_images', exist_ok=True)

# Define test images with different colors and room names
test_images = [
    {'name': 'living_room.jpg', 'color': (150, 200, 220), 'text': 'Living Room'},
    {'name': 'kitchen.jpg', 'color': (220, 200, 150), 'text': 'Kitchen'},
    {'name': 'bedroom.jpg', 'color': (200, 150, 220), 'text': 'Master Bedroom'},
    {'name': 'exterior.jpg', 'color': (150, 220, 150), 'text': 'Front Exterior'},
]

# Create each test image
for img_data in test_images:
    # Create image with room color
    img = Image.new('RGB', (1920, 1080), img_data['color'])
    draw = ImageDraw.Draw(img)
    
    # Add some geometric shapes to make camera movement visible
    # Add corner markers
    marker_size = 100
    draw.rectangle([0, 0, marker_size, marker_size], fill=(50, 50, 50))
    draw.rectangle([1920-marker_size, 0, 1920, marker_size], fill=(50, 50, 50))
    draw.rectangle([0, 1080-marker_size, marker_size, 1080], fill=(50, 50, 50))
    draw.rectangle([1920-marker_size, 1080-marker_size, 1920, 1080], fill=(50, 50, 50))
    
    # Add center cross
    center_x, center_y = 960, 540
    cross_size = 200
    draw.line([center_x - cross_size, center_y, center_x + cross_size, center_y], fill=(0, 0, 0), width=5)
    draw.line([center_x, center_y - cross_size, center_x, center_y + cross_size], fill=(0, 0, 0), width=5)
    
    # Add room text
    try:
        font = ImageFont.truetype("arial.ttf", 72)
    except:
        font = None
    
    text = img_data['text']
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (1920 - text_width) // 2
    text_y = (1080 - text_height) // 2 - 100
    
    # Draw text with shadow
    draw.text((text_x + 3, text_y + 3), text, fill=(0, 0, 0), font=font)
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # Add grid pattern to see movement better
    for x in range(0, 1920, 120):
        draw.line([x, 0, x, 1080], fill=(100, 100, 100), width=1)
    for y in range(0, 1080, 120):
        draw.line([0, y, 1920, y], fill=(100, 100, 100), width=1)
    
    # Save image
    img.save(f'test_images/{img_data["name"]}', quality=95)
    print(f"Created {img_data['name']}")

print("Test images created successfully!")