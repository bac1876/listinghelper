"""Test imageio video generator"""
import os
from imageio_video_generator import create_imageio_video

test_images = [
    'test_images/living_room.jpg',
    'test_images/kitchen.jpg', 
    'test_images/bedroom.jpg',
    'test_images/exterior.jpg'
]

# Filter existing images
existing_images = [img for img in test_images if os.path.exists(img)]

if existing_images:
    print(f"Testing with {len(existing_images)} images...")
    try:
        output = create_imageio_video(existing_images, 'test_imageio.mp4')
        print(f"Success! Created: {output}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No test images found")