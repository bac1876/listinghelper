"""
FFmpeg Watermark Integration
Extends the existing FFmpeg video generation with watermark overlay support
"""

import os
import subprocess
import logging
import tempfile
from typing import Optional, List
from watermark_config import watermark_manager, WatermarkConfig

logger = logging.getLogger(__name__)

def add_watermark_to_video(input_video_path: str, output_video_path: str, 
                          watermark_id: str, ffmpeg_binary: str = None) -> bool:
    """
    Add watermark to an existing video file
    
    Args:
        input_video_path: Path to input video
        output_video_path: Path for output video with watermark
        watermark_id: ID of watermark to apply
        ffmpeg_binary: FFmpeg binary path (auto-detected if None)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get watermark configuration
        watermark_config = watermark_manager.get_watermark(watermark_id)
        if not watermark_config:
            logger.error(f"Watermark not found: {watermark_id}")
            return False
        
        if not watermark_config.filepath or not os.path.exists(watermark_config.filepath):
            logger.error(f"Watermark file not found: {watermark_config.filepath}")
            return False
        
        # Get FFmpeg binary
        if not ffmpeg_binary:
            from ffmpeg_ken_burns import get_ffmpeg_binary
            ffmpeg_binary = get_ffmpeg_binary()
            if not ffmpeg_binary:
                logger.error("FFmpeg binary not found")
                return False
        
        # Get video dimensions
        video_width, video_height = _get_video_dimensions(input_video_path, ffmpeg_binary)
        if not video_width or not video_height:
            logger.warning("Could not detect video dimensions, using defaults")
            video_width, video_height = 1920, 1080
        
        # Generate watermark overlay filter
        overlay_filter = watermark_config.get_ffmpeg_overlay_filter(video_width, video_height)
        if not overlay_filter:
            logger.error("Could not generate overlay filter")
            return False
        
        # Build FFmpeg command
        cmd = [
            ffmpeg_binary,
            '-i', input_video_path,  # Input video
            '-i', watermark_config.filepath,  # Watermark image
            '-filter_complex', overlay_filter,
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-c:v', 'libx264',  # Video codec
            '-preset', 'fast',  # Encoding speed
            '-crf', '20',  # Quality
            '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
            '-movflags', '+faststart',  # Optimize for web streaming
            '-y',  # Overwrite output file
            output_video_path
        ]
        
        logger.info(f"Adding watermark to video: {input_video_path}")
        logger.debug(f"FFmpeg watermark command: {' '.join(cmd)}")
        
        # Execute FFmpeg command
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            shell=(os.name == 'nt'),
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg watermark error: {result.stderr}")
            logger.error(f"FFmpeg watermark stdout: {result.stdout}")
            return False
        
        # Verify output file
        if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
            file_size = os.path.getsize(output_video_path) / 1024 / 1024
            logger.info(f"Watermarked video created: {output_video_path} ({file_size:.2f} MB)")
            return True
        else:
            logger.error("Output video file not created or is empty")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg watermark process timed out")
        return False
    except Exception as e:
        logger.error(f"Error adding watermark to video: {e}")
        return False

def create_ken_burns_video_with_watermark(image_paths: List[str], output_path: str, 
                                        job_id: str, watermark_id: Optional[str] = None, 
                                        quality: Optional[str] = None) -> Optional[str]:
    """
    Create Ken Burns video with optional watermark overlay
    
    Args:
        image_paths: List of image file paths
        output_path: Output video file path
        job_id: Job ID for tracking
        watermark_id: Optional watermark ID to apply
        quality: Quality preset
        
    Returns:
        str: Path to generated video file, or None if failed
    """
    try:
        # First create the video without watermark
        from ffmpeg_ken_burns import create_ken_burns_video
        
        # If no watermark, use existing function
        if not watermark_id:
            return create_ken_burns_video(image_paths, output_path, job_id, quality)
        
        # Create temporary video without watermark first
        temp_video = None
        try:
            temp_dir = tempfile.mkdtemp()
            temp_video = os.path.join(temp_dir, f"temp_{job_id}.mp4")
            
            logger.info("Creating base video without watermark...")
            base_video = create_ken_burns_video(image_paths, temp_video, job_id, quality)
            
            if not base_video or not os.path.exists(base_video):
                logger.error("Failed to create base video")
                return None
            
            logger.info("Adding watermark to video...")
            success = add_watermark_to_video(base_video, output_path, watermark_id)
            
            if success:
                logger.info(f"Ken Burns video with watermark created: {output_path}")
                return output_path
            else:
                logger.warning("Failed to add watermark, returning base video")
                # Copy base video to output path as fallback
                import shutil
                shutil.copy2(base_video, output_path)
                return output_path
                
        finally:
            # Clean up temporary files
            if temp_video and os.path.exists(temp_video):
                try:
                    os.remove(temp_video)
                except:
                    pass
            try:
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error creating Ken Burns video with watermark: {e}")
        # Fallback to regular video generation
        try:
            from ffmpeg_ken_burns import create_ken_burns_video
            return create_ken_burns_video(image_paths, output_path, job_id, quality)
        except Exception as fallback_error:
            logger.error(f"Fallback video generation also failed: {fallback_error}")
            return None

def _get_video_dimensions(video_path: str, ffmpeg_binary: str) -> tuple:
    """
    Get video dimensions using ffprobe
    
    Returns:
        tuple: (width, height) or (None, None) if failed
    """
    try:
        # Try ffprobe first
        ffprobe_binary = ffmpeg_binary.replace('ffmpeg', 'ffprobe')
        if not os.path.exists(ffprobe_binary):
            # Try imageio-ffmpeg ffprobe
            try:
                import imageio_ffmpeg as ffmpeg
                ffprobe_binary = ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
            except:
                ffprobe_binary = 'ffprobe'
        
        cmd = [
            ffprobe_binary,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'v:0',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            streams = data.get('streams', [])
            if streams:
                stream = streams[0]
                width = stream.get('width')
                height = stream.get('height')
                if width and height:
                    logger.debug(f"Detected video dimensions: {width}x{height}")
                    return int(width), int(height)
        
        # Fallback: try with ffmpeg
        cmd = [
            ffmpeg_binary,
            '-i', video_path,
            '-t', '1',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            '-f', 'null',
            '-'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        # Parse dimensions from ffmpeg output
        for line in result.stderr.split('\n'):
            if 'Stream #0:0' in line and 'Video:' in line:
                # Look for pattern like "1920x1080"
                import re
                match = re.search(r'(\d+)x(\d+)', line)
                if match:
                    width, height = match.groups()
                    logger.debug(f"Parsed video dimensions: {width}x{height}")
                    return int(width), int(height)
        
    except Exception as e:
        logger.warning(f"Could not get video dimensions: {e}")
    
    return None, None

def apply_multiple_watermarks(input_video_path: str, output_video_path: str, 
                            watermark_ids: List[str], ffmpeg_binary: str = None) -> bool:
    """
    Apply multiple watermarks to a video
    
    Args:
        input_video_path: Path to input video
        output_video_path: Path for output video
        watermark_ids: List of watermark IDs to apply
        ffmpeg_binary: FFmpeg binary path
        
    Returns:
        bool: True if successful
    """
    if not watermark_ids:
        return False
    
    try:
        current_input = input_video_path
        
        for i, watermark_id in enumerate(watermark_ids):
            is_last = (i == len(watermark_ids) - 1)
            current_output = output_video_path if is_last else tempfile.mktemp(suffix='.mp4')
            
            success = add_watermark_to_video(current_input, current_output, watermark_id, ffmpeg_binary)
            
            if not success:
                logger.error(f"Failed to apply watermark {watermark_id}")
                # Clean up temporary files
                if not is_last and os.path.exists(current_output):
                    os.remove(current_output)
                return False
            
            # Clean up previous temporary file
            if i > 0 and current_input != input_video_path and os.path.exists(current_input):
                os.remove(current_input)
            
            current_input = current_output
        
        logger.info(f"Applied {len(watermark_ids)} watermarks successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error applying multiple watermarks: {e}")
        return False

def validate_watermark_compatibility(watermark_id: str, video_width: int = 1920, 
                                   video_height: int = 1080) -> dict:
    """
    Validate that a watermark is compatible with video dimensions
    
    Returns:
        dict: Validation result with recommendations
    """
    try:
        config = watermark_manager.get_watermark(watermark_id)
        if not config:
            return {'valid': False, 'error': 'Watermark not found'}
        
        if not config.filepath or not os.path.exists(config.filepath):
            return {'valid': False, 'error': 'Watermark file not found'}
        
        # Check image size
        from PIL import Image
        with Image.open(config.filepath) as img:
            watermark_width = int(video_width * config.scale)
            watermark_height = int(video_height * config.scale)
            
            result = {
                'valid': True,
                'watermark_dimensions': (img.width, img.height),
                'scaled_dimensions': (watermark_width, watermark_height),
                'video_dimensions': (video_width, video_height),
                'config': config.to_dict(),
                'recommendations': []
            }
            
            # Add recommendations
            if config.scale < 0.05:
                result['recommendations'].append('Watermark might be too small to be visible')
            elif config.scale > 0.3:
                result['recommendations'].append('Watermark might be too large and intrusive')
            
            if config.opacity < 0.3:
                result['recommendations'].append('Watermark might be too transparent')
            elif config.opacity > 0.9:
                result['recommendations'].append('Watermark might be too opaque')
            
            return result
            
    except Exception as e:
        logger.error(f"Error validating watermark compatibility: {e}")
        return {'valid': False, 'error': str(e)}