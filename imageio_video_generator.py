"""
Video generator using imageio - more reliable than OpenCV for video writing
"""
import os
import logging
import numpy as np
from PIL import Image, ImageEnhance
import gc

logger = logging.getLogger(__name__)

try:
    import imageio
    import imageio_ffmpeg
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False
    logger.error("imageio not available")

def create_imageio_video(image_paths, output_path, fps=24, duration_per_image=3.0):
    """Create video using imageio with Ken Burns effects"""
    
    if not IMAGEIO_AVAILABLE:
        raise ImportError("imageio not available")
    
    # Video parameters
    width, height = 854, 480
    
    # Get ffmpeg executable
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    logger.info(f"Using FFmpeg: {ffmpeg_exe}")
    
    # Create writer with explicit codec settings for maximum compatibility
    writer = imageio.get_writer(
        output_path,
        fps=fps,
        codec='libx264',
        quality=8,
        ffmpeg_params=[
            '-pix_fmt', 'yuv420p',  # Standard pixel format
            '-profile:v', 'baseline',  # Most compatible H.264 profile
            '-level', '3.0',  # Compatible with most devices
            '-crf', '23',
            '-preset', 'medium',
            '-movflags', '+faststart',
            '-vf', 'format=yuv420p'  # Force pixel format conversion
        ]
    )
    
    try:
        for i, img_path in enumerate(image_paths):
            logger.info(f"Processing image {i+1}/{len(image_paths)}: {os.path.basename(img_path)}")
            
            # Load and prepare image
            with Image.open(img_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Enhance slightly
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
                
                # Calculate dimensions for Ken Burns effect
                img_aspect = img.width / img.height
                frame_aspect = width / height
                
                # Make image 30% larger for zoom effect
                scale = 1.3
                if img_aspect > frame_aspect:
                    new_height = int(height * scale)
                    new_width = int(new_height * img_aspect)
                else:
                    new_width = int(width * scale)
                    new_height = int(new_width / img_aspect)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img_array = np.array(img)
            
            # Generate frames with Ken Burns effect
            num_frames = int(duration_per_image * fps)
            
            for frame_idx in range(num_frames):
                t = frame_idx / (num_frames - 1) if num_frames > 1 else 0
                
                # Simple zoom effect
                zoom = 1.0 + 0.2 * t  # Zoom from 1.0 to 1.2
                
                # Calculate viewport
                viewport_w = int(width / zoom)
                viewport_h = int(height / zoom)
                
                # Center with slight pan
                center_x = new_width // 2 + int(50 * t)  # Pan right
                center_y = new_height // 2
                
                # Extract region
                x1 = max(0, center_x - viewport_w // 2)
                y1 = max(0, center_y - viewport_h // 2)
                x2 = min(new_width, x1 + viewport_w)
                y2 = min(new_height, y1 + viewport_h)
                
                # Extract and resize frame
                frame = img_array[y1:y2, x1:x2]
                frame = Image.fromarray(frame)
                frame = frame.resize((width, height), Image.Resampling.LANCZOS)
                frame_array = np.array(frame)
                
                # Write frame
                writer.append_data(frame_array)
            
            # Free memory
            del img_array
            gc.collect()
        
        # Close writer
        writer.close()
        
        # Verify output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            logger.info(f"Video created: {output_path} ({file_size / 1024 / 1024:.2f} MB)")
            return output_path
        else:
            raise ValueError("Failed to create video file")
            
    except Exception as e:
        logger.error(f"Error creating video: {e}")
        if 'writer' in locals():
            writer.close()
        raise

# Export
__all__ = ['create_imageio_video']