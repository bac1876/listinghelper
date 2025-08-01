"""
FFmpeg Ken Burns Video Generator
Creates professional MP4 videos with cinematic Ken Burns effects
"""

import os
import subprocess
import logging
import tempfile
import shutil
from PIL import Image

logger = logging.getLogger(__name__)

def get_ffmpeg_binary():
    """Get FFmpeg binary with multiple fallback options"""
    ffmpeg_binary = None
    
    # Try imageio-ffmpeg first
    try:
        import imageio_ffmpeg as ffmpeg
        ffmpeg_binary = ffmpeg.get_ffmpeg_exe()
        # Test if it actually works
        result = subprocess.run([ffmpeg_binary, '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Using imageio-ffmpeg binary: {ffmpeg_binary}")
            return ffmpeg_binary
    except Exception as e:
        logger.warning(f"imageio-ffmpeg not available or not working: {e}")
    
    # Try system ffmpeg
    for cmd in ['ffmpeg', 'ffmpeg.exe']:
        try:
            result = subprocess.run([cmd, '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Using system ffmpeg: {cmd}")
                return cmd
        except Exception as e:
            logger.warning(f"System ffmpeg '{cmd}' not available: {e}")
    
    # Try common installation paths
    common_paths = [
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            try:
                result = subprocess.run([path, '-version'], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Using ffmpeg at: {path}")
                    return path
            except Exception as e:
                logger.warning(f"FFmpeg at '{path}' not working: {e}")
    
    logger.error("No working FFmpeg binary found")
    return None

FFMPEG_BINARY = get_ffmpeg_binary()

def create_ken_burns_video(image_paths, output_path, job_id, quality=None):
    """
    Create a Ken Burns effect video using FFmpeg
    Returns the path to the generated MP4 file
    
    Args:
        image_paths: List of image file paths
        output_path: Output video file path
        job_id: Job ID for tracking
        quality: Quality preset ('deployment', 'medium', 'high', 'premium') or None for auto-detection
    """
    
    # Try professional virtual tour first
    try:
        logger.info("Creating professional virtual tour...")
        
        # Set environment variable for Railway
        if os.environ.get('RAILWAY_STATIC_URL') or os.environ.get('RAILWAY_GIT_COMMIT_SHA'):
            logger.info("Detected Railway environment, using optimized tour")
            os.environ['RAILWAY_ENVIRONMENT'] = '1'
        
        # Try to log memory usage if psutil is available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            logger.info(f"Current memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        except ImportError:
            logger.info("psutil not available, continuing without memory monitoring")
        
        from professional_virtual_tour import create_professional_tour
        return create_professional_tour(image_paths, output_path, job_id, quality=quality)
    except Exception as e:
        logger.warning(f"Professional tour failed, trying imageio: {e}")
        
        # Try premium imageio as second option
        try:
            from imageio_video_generator import create_imageio_video
            
            # Use quality settings if specified
            if quality == 'premium':
                logger.info("Using premium imageio settings")
                return create_imageio_video(image_paths, output_path, fps=60, duration_per_image=8.0)
            elif quality in ['deployment', 'medium']:
                logger.info(f"Using {quality} imageio settings")
                return create_imageio_video(image_paths, output_path, fps=24, duration_per_image=3.0)
            elif not os.environ.get('RAILWAY_ENVIRONMENT'):
                logger.info("Using premium imageio settings for best quality")
                return create_imageio_video(image_paths, output_path, fps=60, duration_per_image=8.0)
            else:
                return create_imageio_video(image_paths, output_path, fps=24, duration_per_image=3.0)
        except Exception as imageio_error:
            logger.warning(f"Imageio failed, trying FFmpeg: {imageio_error}")
    
    # Video parameters
    fps = 25
    duration_per_image = 4  # seconds
    video_width = 1920
    video_height = 1080
    
    # Create a temporary directory for processed images
    temp_dir = tempfile.mkdtemp()
    
    # Check if FFmpeg is available
    if not FFMPEG_BINARY:
        logger.error("FFmpeg binary not found, cannot create video with FFmpeg")
        raise Exception("FFmpeg not available")
    
    # Log FFmpeg binary being used
    logger.info(f"Using FFmpeg binary: {FFMPEG_BINARY}")
    
    try:
        # First, prepare images for video processing
        processed_images = []
        for i, img_path in enumerate(image_paths):
            try:
                # Open and process image
                with Image.open(img_path) as img:
                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Calculate aspect ratios
                    img_aspect = img.width / img.height
                    video_aspect = video_width / video_height
                    
                    # Resize image to cover the video frame completely
                    if img_aspect > video_aspect:
                        # Image is wider - fit to height
                        new_height = video_height
                        new_width = int(video_height * img_aspect)
                    else:
                        # Image is taller - fit to width
                        new_width = video_width
                        new_height = int(video_width / img_aspect)
                    
                    # Add padding to ensure we have room for Ken Burns movement
                    padding = 1.3  # 30% extra for zoom/pan
                    new_width = int(new_width * padding)
                    new_height = int(new_height * padding)
                    
                    # Resize with high quality
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save processed image
                    processed_path = os.path.join(temp_dir, f'img_{i:04d}.jpg')
                    resized.save(processed_path, 'JPEG', quality=95)
                    processed_images.append(processed_path)
                    
                    logger.info(f"Processed image {i}: {new_width}x{new_height}")
                    
            except Exception as e:
                logger.error(f"Error processing image {i}: {e}")
                continue
        
        if not processed_images:
            raise Exception("No images could be processed")
        
        # Create input file for FFmpeg concat
        concat_file = os.path.join(temp_dir, 'input.txt')
        with open(concat_file, 'w') as f:
            for img_path in processed_images:
                # Each image needs to be specified with duration
                f.write(f"file '{img_path}'\n")
                f.write(f"duration {duration_per_image}\n")
            # Last image needs to be specified again without duration
            f.write(f"file '{processed_images[-1]}'\n")
        
        # Build FFmpeg command with Ken Burns effects
        # We'll create individual segments with different Ken Burns effects, then concatenate
        segments = []
        
        for i, img_path in enumerate(processed_images):
            segment_path = os.path.join(temp_dir, f'segment_{i:04d}.mp4')
            
            # Choose Ken Burns effect based on image index
            if i % 4 == 0:
                # Zoom in from center
                zoompan = f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duration_per_image*fps}:s={video_width}x{video_height}:fps={fps}"
            elif i % 4 == 1:
                # Zoom out to center
                zoompan = f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={duration_per_image*fps}:s={video_width}x{video_height}:fps={fps}"
            elif i % 4 == 2:
                # Pan left to right with slight zoom
                zoompan = f"zoompan=z='1.3':x='if(lte(on,1),(iw-iw/zoom)/2,x-1)':y='ih/2-(ih/zoom/2)':d={duration_per_image*fps}:s={video_width}x{video_height}:fps={fps}"
            else:
                # Pan right to left with zoom in
                zoompan = f"zoompan=z='min(zoom+0.0015,1.5)':x='if(lte(on,1),(iw-iw/zoom)/2,x+1)':y='ih/2-(ih/zoom/2)':d={duration_per_image*fps}:s={video_width}x{video_height}:fps={fps}"
            
            # Create segment with Ken Burns effect
            cmd = [
                FFMPEG_BINARY,
                '-loop', '1',
                '-i', img_path,
                '-vf', zoompan,
                '-c:v', 'libx264',
                '-t', str(duration_per_image),
                '-pix_fmt', 'yuv420p',
                '-preset', 'fast',
                '-crf', '20',
                '-y',
                segment_path
            ]
            
            logger.info(f"Creating segment {i} with Ken Burns effect...")
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
                
                if result.returncode != 0:
                    logger.error(f"FFmpeg error for segment {i}: {result.stderr}")
                    logger.error(f"FFmpeg stdout: {result.stdout}")
                    continue
                
                # Verify segment was created and has size
                if os.path.exists(segment_path) and os.path.getsize(segment_path) > 0:
                    segments.append(segment_path)
                    logger.info(f"Segment {i} created successfully: {os.path.getsize(segment_path) / 1024:.2f} KB")
                else:
                    logger.error(f"Segment {i} was not created or is empty")
            except Exception as e:
                logger.error(f"Error creating segment {i}: {e}")
                continue
        
        if not segments:
            raise Exception("No video segments could be created")
        
        # Create concat file for segments
        segments_file = os.path.join(temp_dir, 'segments.txt')
        with open(segments_file, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
        
        # Concatenate all segments with crossfade transitions
        logger.info("Concatenating segments with transitions...")
        
        # First, concatenate without transitions
        temp_output = os.path.join(temp_dir, 'temp_concat.mp4')
        concat_cmd = [
            FFMPEG_BINARY,
            '-f', 'concat',
            '-safe', '0',
            '-i', segments_file,
            '-c', 'copy',
            '-y',
            temp_output
        ]
        
        try:
            result = subprocess.run(concat_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
            
            if result.returncode != 0:
                logger.error(f"Concatenation error: {result.stderr}")
                # Fallback to simple concat without transitions
                if segments:
                    shutil.copy(segments[0], output_path)
                    logger.warning("Used first segment as fallback output")
                else:
                    raise Exception("No segments available for concatenation")
            else:
                # Add fade transitions between segments
                final_cmd = [
                    FFMPEG_BINARY,
                    '-i', temp_output,
                    '-vf', 'fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5',
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '20',
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-y',
                    output_path
                ]
            
                try:
                    result = subprocess.run(final_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
                    
                    if result.returncode != 0:
                        logger.error(f"Final processing error: {result.stderr}")
                        # Use temp output as fallback
                        if os.path.exists(temp_output):
                            shutil.copy(temp_output, output_path)
                            logger.warning("Used concatenated output without fade effects")
                        else:
                            raise Exception("No temporary output available")
                except Exception as e:
                    logger.error(f"Error in final processing: {e}")
                    if os.path.exists(temp_output):
                        shutil.copy(temp_output, output_path)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Error in FFmpeg processing: {e}")
            raise
        
        # Verify final output
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 0:
                logger.info(f"Ken Burns video created: {output_path} (size: {file_size / 1024 / 1024:.2f} MB)")
                
                # Ensure video is playable
                try:
                    from ensure_playable_video import ensure_video_is_playable
                    final_path = ensure_video_is_playable(output_path)
                    if final_path:
                        return final_path
                except Exception as e:
                    logger.warning(f"Could not verify video compatibility: {e}")
                
                return output_path
            else:
                logger.error(f"Output file is empty: {output_path}")
                raise ValueError("Generated video file is empty")
        else:
            logger.error(f"Output file not found: {output_path}")
            raise ValueError("Failed to create video file")
        
    except Exception as e:
        logger.error(f"Error creating Ken Burns video: {e}")
        
        # Try simple video generation as fallback
        try:
            logger.info("Attempting simple video generation as fallback...")
            from simple_video_generator import create_simple_video
            return create_simple_video(image_paths, output_path, job_id)
        except Exception as fallback_error:
            logger.error(f"Fallback video generation also failed: {fallback_error}")
            raise e
    
    finally:
        # Clean up temporary files
        try:
            shutil.rmtree(temp_dir)
        except:
            pass