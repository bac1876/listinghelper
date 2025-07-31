"""
Ensure videos are playable by using the most compatible settings
"""
import os
import logging
import subprocess
import shutil
import tempfile

logger = logging.getLogger(__name__)

def convert_to_compatible_mp4(input_path, output_path):
    """
    Convert any video to a highly compatible MP4 using FFmpeg
    """
    # Try to use imageio-ffmpeg first
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except:
        ffmpeg_exe = 'ffmpeg'
    
    # Create temp file for conversion
    temp_output = tempfile.mktemp(suffix='.mp4')
    
    # Use the most compatible H.264 settings
    cmd = [
        ffmpeg_exe,
        '-i', input_path,
        '-c:v', 'libx264',      # H.264 codec
        '-preset', 'medium',     # Balance between speed and compression
        '-crf', '23',           # Quality (lower = better, 23 is good)
        '-pix_fmt', 'yuv420p',  # Most compatible pixel format
        '-profile:v', 'baseline', # Most compatible H.264 profile
        '-level', '3.0',        # Compatible with most devices
        '-movflags', '+faststart', # Web optimization
        '-y',                   # Overwrite output
        temp_output
    ]
    
    try:
        logger.info(f"Converting video to compatible MP4 format...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(temp_output):
            # Move to final location
            shutil.move(temp_output, output_path)
            logger.info(f"Successfully converted to compatible MP4: {output_path}")
            return True
        else:
            logger.error(f"FFmpeg conversion failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error converting video: {e}")
        return False
    finally:
        # Clean up temp file if it exists
        if os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass

def ensure_video_is_playable(video_path):
    """
    Check if video is playable and convert if necessary
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False
    
    # Check file extension
    if not video_path.lower().endswith('.mp4'):
        # Convert to MP4
        mp4_path = video_path.rsplit('.', 1)[0] + '.mp4'
        if convert_to_compatible_mp4(video_path, mp4_path):
            # Remove original and rename
            try:
                os.remove(video_path)
            except:
                pass
            return mp4_path
        return False
    
    # Try to probe the video with ffmpeg
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except:
        ffmpeg_exe = 'ffmpeg'
    
    probe_cmd = [
        ffmpeg_exe,
        '-i', video_path,
        '-f', 'null',
        '-'
    ]
    
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        # Check if it mentions RGBA or other problematic codecs
        if 'rgba' in result.stderr.lower() or result.returncode != 0:
            logger.warning(f"Video may have compatibility issues, converting...")
            # Create a new filename for the converted version
            base, ext = os.path.splitext(video_path)
            new_path = f"{base}_compatible{ext}"
            
            if convert_to_compatible_mp4(video_path, new_path):
                # Replace original with converted version
                try:
                    os.remove(video_path)
                    os.rename(new_path, video_path)
                except:
                    return new_path
        
        return video_path
        
    except Exception as e:
        logger.error(f"Error probing video: {e}")
        return video_path