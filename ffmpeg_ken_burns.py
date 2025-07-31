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

try:
    import imageio_ffmpeg as ffmpeg
    FFMPEG_BINARY = ffmpeg.get_ffmpeg_exe()
    logger.info(f"Using imageio-ffmpeg binary: {FFMPEG_BINARY}")
except:
    FFMPEG_BINARY = 'ffmpeg'
    logger.info("Using system ffmpeg")

def create_ken_burns_video(image_paths, output_path, job_id):
    """
    Create a Ken Burns effect video using FFmpeg
    Returns the path to the generated MP4 file
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
        return create_professional_tour(image_paths, output_path, job_id)
    except Exception as e:
        logger.warning(f"Professional tour failed, trying FFmpeg: {e}")
    
    # Video parameters
    fps = 25
    duration_per_image = 4  # seconds
    video_width = 1920
    video_height = 1080
    
    # Create a temporary directory for processed images
    temp_dir = tempfile.mkdtemp()
    
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
            logger.info(f"FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error for segment {i}: {result.stderr}")
                logger.error(f"FFmpeg stdout: {result.stdout}")
                continue
            
            segments.append(segment_path)
        
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
        
        result = subprocess.run(concat_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
        
        if result.returncode != 0:
            logger.error(f"Concatenation error: {result.stderr}")
            # Fallback to simple concat without transitions
            shutil.copy(segments[0], output_path)
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
            
            result = subprocess.run(final_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
            
            if result.returncode != 0:
                logger.error(f"Final processing error: {result.stderr}")
                # Use temp output as fallback
                shutil.copy(temp_output, output_path)
        
        logger.info(f"Ken Burns video created: {output_path}")
        return output_path
        
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