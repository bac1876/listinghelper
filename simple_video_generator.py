"""
Simple video generator using imageio-ffmpeg
Fallback for when complex FFmpeg commands fail
"""

import os
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

try:
    import imageio
    import imageio_ffmpeg as ffmpeg
    IMAGEIO_AVAILABLE = True
    logger.info("imageio available for video generation")
except ImportError:
    IMAGEIO_AVAILABLE = False
    logger.warning("imageio not available")

def create_simple_video(image_paths, output_path, job_id):
    """
    Create a simple video from images using imageio
    This is a fallback when FFmpeg commands fail
    """
    
    if not IMAGEIO_AVAILABLE:
        raise Exception("imageio not available for video generation")
    
    try:
        # Video parameters
        fps = 2  # 2 fps for slower transitions
        video_width = 1920
        video_height = 1080
        
        # Create writer
        writer = imageio.get_writer(
            output_path, 
            fps=fps,
            codec='libx264',
            quality=8,
            pixelformat='yuv420p',
            ffmpeg_params=['-crf', '23']
        )
        
        for img_path in image_paths:
            try:
                # Open and process image
                with Image.open(img_path) as img:
                    # Convert to RGB
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Calculate aspect ratios
                    img_aspect = img.width / img.height
                    video_aspect = video_width / video_height
                    
                    # Resize to fit video frame
                    if img_aspect > video_aspect:
                        # Image is wider - fit to width
                        new_width = video_width
                        new_height = int(video_width / img_aspect)
                    else:
                        # Image is taller - fit to height
                        new_height = video_height
                        new_width = int(video_height * img_aspect)
                    
                    # Resize image
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Create black background
                    frame = Image.new('RGB', (video_width, video_height), (0, 0, 0))
                    
                    # Paste image centered
                    x = (video_width - new_width) // 2
                    y = (video_height - new_height) // 2
                    frame.paste(img, (x, y))
                    
                    # Convert to numpy array
                    frame_array = np.array(frame)
                    
                    # Write multiple frames for duration
                    frames_per_image = fps * 3  # 3 seconds per image
                    for _ in range(frames_per_image):
                        writer.append_data(frame_array)
                    
                    logger.info(f"Added image to video: {img_path}")
                    
            except Exception as e:
                logger.error(f"Error processing image {img_path}: {e}")
                continue
        
        # Close writer
        writer.close()
        
        logger.info(f"Simple video created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating simple video: {e}")
        raise