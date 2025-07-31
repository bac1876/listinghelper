"""
Create a compatible MP4 video using direct OpenCV with MP4V codec
"""
import os
import cv2
import numpy as np
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_compatible_mp4(image_paths, output_path):
    """Create MP4 with most compatible settings"""
    
    # Video settings
    fps = 24
    width, height = 854, 480
    
    # Try different codecs in order of compatibility
    codecs = [
        ('MP4V', cv2.VideoWriter_fourcc(*'MP4V')),
        ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),
        ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
        ('MJPG', cv2.VideoWriter_fourcc(*'MJPG'))
    ]
    
    writer = None
    used_codec = None
    
    for codec_name, fourcc in codecs:
        try:
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
            if writer.isOpened():
                logger.info(f"Using codec: {codec_name}")
                used_codec = codec_name
                break
            else:
                writer.release()
                writer = None
        except Exception as e:
            logger.warning(f"Failed with codec {codec_name}: {e}")
    
    if not writer or not writer.isOpened():
        raise ValueError("Could not create video writer")
    
    # Process images
    for i, img_path in enumerate(image_paths):
        logger.info(f"Processing image {i+1}/{len(image_paths)}")
        
        # Load and resize image
        with Image.open(img_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Simple resize to fit frame
            img_aspect = img.width / img.height
            frame_aspect = width / height
            
            if img_aspect > frame_aspect:
                new_width = width
                new_height = int(width / img_aspect)
            else:
                new_height = height
                new_width = int(height * img_aspect)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create black frame and paste image centered
            frame = Image.new('RGB', (width, height), (0, 0, 0))
            x = (width - new_width) // 2
            y = (height - new_height) // 2
            frame.paste(img, (x, y))
            
            # Convert to numpy array
            frame_array = np.array(frame)
            
            # Convert RGB to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)
            
            # Write frame multiple times for duration (3 seconds per image)
            frames_per_image = int(fps * 3)
            for _ in range(frames_per_image):
                success = writer.write(frame_bgr)
                if not success:
                    logger.warning("Failed to write frame")
    
    # Release writer
    writer.release()
    
    # Verify output
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        logger.info(f"Video created: {output_path} ({size / 1024 / 1024:.2f} MB) using codec: {used_codec}")
        return output_path
    else:
        raise ValueError("Failed to create video")

if __name__ == "__main__":
    test_images = [
        'test_images/living_room.jpg',
        'test_images/kitchen.jpg',
        'test_images/bedroom.jpg',
        'test_images/exterior.jpg'
    ]
    
    # Filter existing images
    existing_images = [img for img in test_images if os.path.exists(img)]
    
    if existing_images:
        output = create_compatible_mp4(existing_images, 'test_compatible.mp4')
        print(f"Created: {output}")
    else:
        print("No test images found")