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
        
        # Create writer with multiple codec fallbacks
        writer = None
        codec_configs = [
            {
                'codec': 'libx264',
                'quality': 8,
                'pixelformat': 'yuv420p',
                'ffmpeg_params': ['-crf', '23', '-preset', 'fast']
            },
            {
                'codec': 'mpeg4',
                'quality': 8,
                'pixelformat': 'yuv420p',
                'ffmpeg_params': ['-q:v', '5']
            },
            {
                'codec': 'mjpeg',
                'quality': 9,
                'ffmpeg_params': ['-q:v', '2']
            }
        ]
        
        for config in codec_configs:
            try:
                writer = imageio.get_writer(
                    output_path, 
                    fps=fps,
                    **config
                )
                logger.info(f"Created video writer with codec: {config['codec']}")
                break
            except Exception as e:
                logger.warning(f"Failed to create writer with codec {config['codec']}: {e}")
                continue
        
        if writer is None:
            raise ValueError("Could not create video writer with any available codec")
        
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
                    
                    # Ensure frame array is correct type
                    if frame_array.dtype != np.uint8:
                        frame_array = frame_array.astype(np.uint8)
                    
                    # Write multiple frames for duration
                    frames_per_image = fps * 3  # 3 seconds per image
                    for _ in range(frames_per_image):
                        try:
                            writer.append_data(frame_array)
                        except Exception as e:
                            logger.error(f"Error writing frame: {e}")
                    
                    logger.info(f"Added image to video: {img_path}")
                    
            except Exception as e:
                logger.error(f"Error processing image {img_path}: {e}")
                continue
        
        # Close writer
        try:
            writer.close()
        except Exception as e:
            logger.error(f"Error closing video writer: {e}")
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 0:
                logger.info(f"Simple video created: {output_path} (size: {file_size / 1024 / 1024:.2f} MB)")
                return output_path
            else:
                logger.error(f"Output file is empty: {output_path}")
                raise ValueError("Generated video file is empty")
        else:
            logger.error(f"Output file not found: {output_path}")
            raise ValueError("Failed to create video file")
        
    except Exception as e:
        logger.error(f"Error creating simple video: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise