from flask import Blueprint, request, jsonify, send_file, redirect
import os
import tempfile
import subprocess
import time
from datetime import datetime, timedelta
import uuid
import base64
import shutil
import threading
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Using storage backend (Bunny.net or ImageKit)
from upload_to_storage import upload_files_to_storage, upload_video_to_storage, get_video_url_storage
# Compatibility aliases
upload_files_to_imagekit = upload_files_to_storage
upload_video_to_imagekit = upload_video_to_storage
get_video_url_imagekit = get_video_url_storage
from github_actions_integration import GitHubActionsIntegration
from PIL import Image
import io

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# Railway storage directory
STORAGE_DIR = '/app/storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# Temporary directory for video processing
TEMP_DIR = os.environ.get('TEMP_DIR', tempfile.gettempdir())
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

# In-memory job tracking with detailed status
active_jobs = {}

def trigger_ffmpeg_fallback(job_id):
    """Trigger local FFmpeg processing as a fallback when GitHub Actions fails"""
    try:
        if job_id not in active_jobs:
            logger.error(f"Job {job_id} not found for FFmpeg fallback")
            return
        
        job = active_jobs[job_id]
        
        # Update status
        job['status'] = 'processing'
        job['current_step'] = 'Falling back to local video generation...'
        job['progress'] = 50
        
        # Get saved files from job
        saved_files = job.get('saved_files', [])
        if not saved_files:
            logger.error(f"No saved files found for job {job_id}")
            job['status'] = 'error'
            job['current_step'] = 'No images available for fallback processing'
            return
        
        # Import FFmpeg Ken Burns function
        from ffmpeg_ken_burns import create_ken_burns_video
        
        # Create output path
        output_filename = f"virtual_tour_{job_id}.mp4"
        output_path = os.path.join(TEMP_DIR, output_filename)
        
        logger.info(f"Starting FFmpeg fallback for job {job_id} with {len(saved_files)} images")
        
        # Get duration setting
        duration_per_image = job.get('duration_per_image', 6)
        
        # Create video with FFmpeg
        try:
            job['current_step'] = 'Generating video with local processor...'
            job['progress'] = 60
            
            created_video = create_ken_burns_video(
                saved_files,
                output_path,
                job_id,
                quality='medium'  # Use medium quality for faster processing
            )
            
            if created_video and os.path.exists(created_video):
                logger.info(f"FFmpeg fallback successful: {created_video}")
                job['video_path'] = created_video
                job['video_available'] = True
                job['status'] = 'completed'
                job['current_step'] = 'Video generated successfully (fallback mode)'
                job['progress'] = 90
                
                # Try to upload to ImageKit
                try:
                    video_url = upload_video_to_storage(created_video, f"tours/videos/{output_filename}")
                    if video_url:
                        job['video_url'] = video_url
                        job['files_generated']['video_url'] = video_url
                        logger.info(f"Fallback video uploaded to ImageKit: {video_url}")
                except Exception as e:
                    logger.error(f"Failed to upload fallback video to ImageKit: {e}")
                    # Video still available locally
                
                job['progress'] = 100
                job['current_step'] = 'Video ready (generated locally)'
            else:
                raise Exception("FFmpeg failed to create video")
                
        except Exception as e:
            logger.error(f"FFmpeg fallback failed: {e}")
            job['status'] = 'error'
            job['current_step'] = f'Video generation failed completely: {str(e)}'
            job['progress'] = 100
            
    except Exception as e:
        logger.error(f"Error in FFmpeg fallback: {e}")
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = f'Fallback failed: {str(e)}'
            active_jobs[job_id]['progress'] = 100

def start_github_actions_polling(job_id, github_job_id):
    """Start a background thread to poll GitHub Actions and then ImageKit for the completed video"""
    def poll_for_video():
        logger.info(f"Starting GitHub Actions polling for job {job_id}, GitHub job ID: {github_job_id}")
        
        max_attempts = 45  # Poll for up to 7.5 minutes (45 * 10 seconds) - reduced for faster fallback
        attempt = 0
        github_actions_complete = False
        video_url = None
        
        while attempt < max_attempts:
            attempt += 1
            
            try:
                # Update progress based on time elapsed
                progress = min(75 + (attempt * 0.4), 95)  # Progress from 75% to 95%
                active_jobs[job_id]['progress'] = int(progress)
                
                # Update status message with time estimate
                remaining_time = (max_attempts - attempt) * 10
                active_jobs[job_id]['current_step'] = f'Rendering with Remotion... (~{remaining_time}s remaining)'
                
                # First, check if GitHub Actions has completed
                if not github_actions_complete and github_actions:
                    try:
                        # Check GitHub Actions workflow status (now returns tuple)
                        workflow_status, error_details = github_actions.get_workflow_status(github_job_id)
                        logger.info(f"GitHub Actions status for {github_job_id}: {workflow_status}")
                        
                        if workflow_status == 'completed':
                            github_actions_complete = True
                            logger.info(f"GitHub Actions completed for job {github_job_id}")
                            
                            # Try to get the artifact with video URL
                            artifact_data = github_actions.get_workflow_artifact(github_job_id)
                            if artifact_data and artifact_data.get('videoUrl'):
                                video_url = artifact_data['videoUrl']
                                logger.info(f"Got video URL from GitHub artifact: {video_url}")
                            else:
                                # Construct ImageKit URL as fallback
                                video_url = get_video_url_imagekit(github_job_id)
                                logger.info(f"Using constructed ImageKit URL: {video_url}")
                        elif workflow_status == 'failed':
                            logger.error(f"GitHub Actions workflow failed for job {github_job_id}: {error_details}")
                            active_jobs[job_id]['status'] = 'error'
                            active_jobs[job_id]['current_step'] = f'Remotion failed: {error_details or "Unknown error"}'
                            active_jobs[job_id]['progress'] = 100
                            active_jobs[job_id]['error_details'] = error_details
                            
                            # Trigger FFmpeg fallback
                            logger.info(f"Attempting FFmpeg fallback for job {job_id}")
                            trigger_ffmpeg_fallback(job_id)
                            return
                    except Exception as e:
                        logger.warning(f"Error checking GitHub Actions status: {e}")
                
                # If GitHub Actions is complete, check if video exists
                if github_actions_complete and video_url:
                    response = requests.head(video_url, timeout=5)
                else:
                    # Still waiting for GitHub Actions
                    time.sleep(10)
                    continue
                
                if response.status_code == 200:
                    # Video found!
                    logger.info(f"Video found on ImageKit for job {job_id}!")
                    
                    # Update job status
                    active_jobs[job_id]['status'] = 'completed'
                    active_jobs[job_id]['progress'] = 100
                    active_jobs[job_id]['current_step'] = 'Video ready!'
                    active_jobs[job_id]['imagekit_video'] = True
                    active_jobs[job_id]['video_available'] = True
                    
                    if 'files_generated' not in active_jobs[job_id]:
                        active_jobs[job_id]['files_generated'] = {}
                    active_jobs[job_id]['files_generated']['imagekit_url'] = video_url
                    
                    logger.info(f"Job {job_id} completed successfully with ImageKit URL: {video_url}")
                    return
                
                elif response.status_code == 404:
                    # Video not ready yet, continue polling
                    logger.debug(f"Attempt {attempt}/{max_attempts}: Video not yet available at {video_url}")
                else:
                    logger.warning(f"Unexpected status {response.status_code} when checking video URL")
                    
            except Exception as e:
                logger.debug(f"Polling attempt {attempt} failed: {e}")
            
            # Wait before next attempt
            time.sleep(10)
        
        # Timeout - video generation took too long, trigger fallback
        logger.error(f"Video polling timeout for job {job_id} after {max_attempts} attempts")
        active_jobs[job_id]['status'] = 'processing'
        active_jobs[job_id]['current_step'] = 'Remotion timeout - switching to local processing...'
        active_jobs[job_id]['progress'] = 50
        
        # Trigger FFmpeg fallback
        logger.info(f"Triggering FFmpeg fallback due to timeout for job {job_id}")
        trigger_ffmpeg_fallback(job_id)
    
    # Start polling in background thread
    polling_thread = threading.Thread(target=poll_for_video, daemon=True)
    polling_thread.start()
    logger.info(f"Started GitHub Actions polling thread for job {job_id}")

# Initialize GitHub Actions integration if configured
github_actions = None
if all([os.environ.get('GITHUB_TOKEN'), os.environ.get('GITHUB_OWNER'), os.environ.get('GITHUB_REPO')]):
    try:
        github_actions = GitHubActionsIntegration()
        logger.info("GitHub Actions integration initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize GitHub Actions: {e}")

def cleanup_old_files():
    """Clean up files older than 24 hours"""
    try:
        if not os.path.exists(STORAGE_DIR):
            return
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for filename in os.listdir(STORAGE_DIR):
            filepath = os.path.join(STORAGE_DIR, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if file_time < cutoff_time:
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old file: {filename}")
                    except:
                        pass
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

def start_cleanup_thread():
    def cleanup_loop():
        while True:
            cleanup_old_files()
            time.sleep(3600)  # Run every hour
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()

# Start cleanup thread when module loads
start_cleanup_thread()

def compress_image(file_obj, filename, max_width=1920, max_height=1080, quality=85):
    """
    Compress and resize image to reduce file size
    
    Args:
        file_obj: File object from request
        filename: Original filename
        max_width: Maximum width (default 1920 for Full HD)
        max_height: Maximum height (default 1080 for Full HD)
        quality: JPEG quality (default 85, good quality with small size)
    
    Returns:
        Compressed image bytes and new filename
    """
    try:
        # Open image with PIL
        img = Image.open(file_obj)
        
        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate new size maintaining aspect ratio
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        
        # Only resize if image is larger than max dimensions
        if original_width > max_width or original_height > max_height:
            if aspect_ratio > max_width / max_height:
                # Image is wider, fit to width
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                # Image is taller, fit to height
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            
            # Resize with high quality
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {original_width}x{original_height} to {new_width}x{new_height}")
        
        # Save to bytes buffer
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Update filename to .jpg
        new_filename = os.path.splitext(filename)[0] + '.jpg'
        
        return output, new_filename
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        # Return original if compression fails
        file_obj.seek(0)
        return file_obj, filename

@virtual_tour_bp.route('/env-check', methods=['GET'])
def env_check():
    """Debug endpoint to check environment variables"""
    env_vars = {}
    
    # Check ImageKit variables
    imagekit_vars = ['IMAGEKIT_PRIVATE_KEY', 'IMAGEKIT_PUBLIC_KEY', 'IMAGEKIT_URL_ENDPOINT']
    for var in imagekit_vars:
        value = os.environ.get(var)
        if value:
            if 'PRIVATE' in var:
                env_vars[var] = f"{value[:20]}..." if len(value) > 20 else "SET"
            elif 'PUBLIC' in var:
                env_vars[var] = f"{value[:20]}..." if len(value) > 20 else "SET"
            else:
                env_vars[var] = value  # URL is not sensitive
        else:
            env_vars[var] = "NOT_SET"
    
    # Check other important vars
    other_vars = ['USE_GITHUB_ACTIONS', 'GITHUB_TOKEN']
    for var in other_vars:
        value = os.environ.get(var)
        if value:
            if 'TOKEN' in var or 'SECRET' in var:
                env_vars[var] = "SET (hidden)"
            else:
                env_vars[var] = value
        else:
            env_vars[var] = "NOT_SET"
    
    # Test ImageKit initialization
    from storage_adapter import test_storage_initialization
    storage_status, backend = test_storage_initialization()
    
    return jsonify({
        'environment_variables': env_vars,
        'storage_initialized': storage_status,
        'storage_backend': backend,
        'railway_deployment': os.environ.get('RAILWAY_ENVIRONMENT', 'NOT_RAILWAY'),
        'python_path': os.environ.get('PYTHONPATH', 'NOT_SET')
    })

@virtual_tour_bp.route('/health', methods=['GET'])
def health_check():
    """Check system health - GitHub Actions, storage backend, and storage"""
    # Check storage backend status
    from storage_adapter import get_storage
    try:
        storage_instance = get_storage()
        storage_configured = True
        backend_name = storage_instance.get_backend_name()
    except:
        storage_configured = False
        backend_name = 'NOT_CONFIGURED'
    
    health_status = {
        'status': 'healthy',
        'storage_writable': False,
        'storage_path': STORAGE_DIR,
        'github_actions_available': github_actions is not None,
        'storage_configured': storage_configured,
        'storage_backend': backend_name,
        'primary_storage': backend_name.upper() if storage_configured else 'NOT_CONFIGURED'
    }
    
    # Check storage
    try:
        test_file = os.path.join(STORAGE_DIR, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        health_status['storage_writable'] = True
    except:
        pass
    
    # Check GitHub Actions
    if github_actions:
        try:
            workflow_status = github_actions.get_workflow_status()
            health_status['github_workflow_status'] = workflow_status
        except:
            pass
    
    return jsonify(health_status)

# REMOVED: GitHub job status endpoint to prevent API rate limit exhaustion
# The Cloudinary polling mechanism handles video status checking without API calls

@virtual_tour_bp.route('/upload', methods=['POST'])
def upload_images():
    """Handle image upload and create virtual tour with improved error recovery"""
    job_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Initialize error recovery
    MAX_RETRIES = 3
    retry_count = 0
    
    try:
        # Check for existing job ID (checking status)
        if request.is_json and 'job_id' in request.get_json():
            check_job_id = request.get_json()['job_id']
            if check_job_id in active_jobs:
                job = active_jobs[check_job_id]
                return jsonify({
                    'job_id': check_job_id,
                    'status': job['status'],
                    'progress': job.get('progress', 0),
                    'current_step': job.get('current_step', ''),
                    'video_available': job.get('video_available', False),
                    'virtual_tour_available': job.get('virtual_tour_available', False),
                                'images_processed': job.get('images_processed', 0),
                    'processing_time': job.get('processing_time', ''),
                    'files_generated': job.get('files_generated', {})
                })
        
        # Initialize job tracking
        active_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'current_step': 'Initializing',
            'video_available': False,
            'virtual_tour_available': False,
            'images_processed': 0,
            'files_generated': {}
        }
        
        # Parse request data
        if request.is_json:
            data = request.get_json()
            image_urls = data.get('images', [])
            property_details = data.get('property_details', {})
            settings = data.get('settings', {})
        else:
            # Handle form data with files
            image_urls = []
            property_details = {}
            settings = {}
        
        # Get property details
        full_address = property_details.get('address', request.form.get('address', 'Beautiful Property'))
        
        # Parse address to extract street and city if it contains a newline
        if '\n' in full_address:
            address_parts = full_address.split('\n', 1)
            address = address_parts[0].strip()  # Street address
            city = address_parts[1].strip() if len(address_parts) > 1 else ''
        else:
            address = full_address
            city = ''  # Don't use default "Your City, State"
        
        details1 = property_details.get('details1', request.form.get('details1', 'Call for viewing'))
        details2 = property_details.get('details2', request.form.get('details2', 'Just Listed'))
        
        agent_name = property_details.get('agent_name', request.form.get('agent_name', 'Your Agent'))
        agent_email = property_details.get('agent_email', request.form.get('agent_email', 'agent@realestate.com'))
        agent_phone = property_details.get('agent_phone', request.form.get('agent_phone', '(555) 123-4567'))
        brand_name = property_details.get('brand_name', request.form.get('brand_name', 'Premium Real Estate'))
        
        # Get settings
        duration_per_image = int(settings.get('durationPerImage', request.form.get('duration_per_image', 8)))
        effect_speed = settings.get('effectSpeed', request.form.get('effect_speed', 'medium'))
        transition_duration = float(settings.get('transitionDuration', request.form.get('transition_duration', 1.5)))
        
        # Get watermark settings if provided
        watermark_id = request.form.get('watermark_id', None)
        if watermark_id and watermark_id.strip():
            # Validate watermark exists
            try:
                from watermark_config import watermark_manager
                watermark_config = watermark_manager.get_watermark(watermark_id)
                if not watermark_config:
                    logger.warning(f"Watermark not found: {watermark_id}")
                    watermark_id = None
                else:
                    logger.info(f"Using watermark: {watermark_id}")
            except Exception as e:
                logger.error(f"Error validating watermark: {e}")
                watermark_id = None
        else:
            watermark_id = None
        
        # Process uploaded files - check both 'files' and 'images' fields
        files = []
        if 'files' in request.files:
            files = request.files.getlist('files')
            logger.info(f"Received {len(files)} files in 'files' field for job {job_id}")
        elif 'images' in request.files:
            files = request.files.getlist('images')
            logger.info(f"Received {len(files)} files in 'images' field for job {job_id}")
        
        if files:
            # Log each file for debugging
            valid_files = []
            for i, file in enumerate(files):
                file_size = len(file.read())
                file.seek(0)  # Reset file pointer after reading
                logger.info(f"  File {i+1}: {file.filename} ({file_size} bytes, type: {file.mimetype})")
                
                # Check file size (max 10MB per image)
                if file_size > 10 * 1024 * 1024:
                    logger.warning(f"  File {i+1} rejected: Too large ({file_size} bytes > 10MB)")
                    continue
                    
                # Check file type
                if not file.mimetype.startswith('image/'):
                    logger.warning(f"  File {i+1} rejected: Invalid type ({file.mimetype})")
                    continue
                    
                valid_files.append(file)
            
            logger.info(f"Valid files after filtering: {len(valid_files)} of {len(files)}")
            files = valid_files
            
            # Create job directory
            job_dir = os.path.join(STORAGE_DIR, job_id)
            os.makedirs(job_dir, exist_ok=True)
            
            # Save uploaded files with compression - BATCH PROCESSING
            saved_files = []
            original_total_size = 0
            compressed_total_size = 0
            
            # Process images in batches of 4 to prevent memory overload
            BATCH_SIZE = 4
            total_files = len(files)
            
            for batch_start in range(0, total_files, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_files)
                batch_files = files[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//BATCH_SIZE + 1} (images {batch_start+1}-{batch_end} of {total_files})")
                active_jobs[job_id]['current_step'] = f'Processing images {batch_start+1}-{batch_end} of {total_files}'
                active_jobs[job_id]['progress'] = int(5 + (batch_end / total_files) * 15)  # Progress from 5% to 20%
                
                for i, file in enumerate(batch_files):
                    actual_index = batch_start + i
                    if file and file.filename:
                        try:
                            # Get original file size
                            file.seek(0, 2)  # Seek to end
                            original_size = file.tell()
                            original_total_size += original_size
                            file.seek(0)  # Reset to beginning
                            
                            # Compress the image
                            compressed_file, compressed_filename = compress_image(file, file.filename)
                            
                            # Save compressed file
                            filename = f"image_{actual_index}_{compressed_filename}"
                            filepath = os.path.join(job_dir, filename)
                            
                            # If compression returned a BytesIO object, save its contents
                            if isinstance(compressed_file, io.BytesIO):
                                with open(filepath, 'wb') as f:
                                    f.write(compressed_file.getvalue())
                                compressed_size = len(compressed_file.getvalue())
                            else:
                                # Fallback: save original file
                                compressed_file.seek(0)
                                with open(filepath, 'wb') as f:
                                    f.write(compressed_file.read())
                                compressed_file.seek(0, 2)
                                compressed_size = compressed_file.tell()
                            
                            compressed_total_size += compressed_size
                            saved_files.append(filepath)
                            
                            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                            logger.info(f"Saved compressed file: {filename} (Original: {original_size/1024:.1f}KB, Compressed: {compressed_size/1024:.1f}KB, Saved: {compression_ratio:.1f}%)")
                            
                        except Exception as e:
                            logger.error(f"Error processing image {actual_index}: {e}")
                            # Continue with next image instead of failing completely
                            continue
                
                # Brief pause between batches to prevent resource exhaustion
                if batch_end < total_files:
                    time.sleep(0.5)  # Half second pause between batches
            
            # Update job progress with compression info
            active_jobs[job_id]['images_processed'] = len(saved_files)
            active_jobs[job_id]['saved_files'] = saved_files  # Store for potential fallback
            if original_total_size > 0:
                total_compression = (1 - compressed_total_size / original_total_size) * 100
                active_jobs[job_id]['current_step'] = f'Compressed {len(saved_files)} images (saved {total_compression:.0f}% space)'
                logger.info(f"Total compression: {original_total_size/1024/1024:.1f}MB -> {compressed_total_size/1024/1024:.1f}MB")
            else:
                active_jobs[job_id]['current_step'] = f'Saved {len(saved_files)} images'
            active_jobs[job_id]['progress'] = 10
            
            # NO FFMPEG FALLBACK - Only use GitHub Actions + Remotion or Cloudinary
            # FFmpeg creates terrible quality videos and is worse than failure
            # UNLESS we have a watermark - then we need local processing
        
        # Check if we should use GitHub Actions for high-quality rendering
        # If watermark is requested, force local processing since GitHub Actions doesn't support watermarks yet
        use_github_actions = os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() == 'true' and github_actions and not watermark_id
        logger.info(f"GitHub Actions enabled: {use_github_actions} (env: {os.environ.get('USE_GITHUB_ACTIONS')}, integration: {github_actions is not None})")
        
        # Prepare image URLs for GitHub Actions
        github_image_urls = image_urls or []
        
        # If we have uploaded files but no URLs, upload them to Cloudinary first
        if use_github_actions and 'saved_files' in locals() and saved_files and not image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Uploading images to ImageKit for GitHub Actions'
                active_jobs[job_id]['progress'] = 40
                
                # Upload files to ImageKit
                logger.info(f"Uploading {len(saved_files)} files to ImageKit...")
                for i, file in enumerate(saved_files):
                    logger.info(f"  Will upload file {i+1}: {os.path.basename(file)}")
                
                # Use storage backend for image uploads
                from storage_adapter import get_storage
                try:
                    storage_instance = get_storage()
                    backend_name = storage_instance.get_backend_name()
                    logger.info(f"Using {backend_name} for image uploads")
                except Exception as e:
                    logger.error(f"Storage backend not configured! {e}")
                    active_jobs[job_id]['status'] = 'error'
                    active_jobs[job_id]['current_step'] = 'Storage backend not configured - cannot proceed'
                    active_jobs[job_id]['error'] = 'Storage configuration missing'
                    raise ValueError("Storage backend not configured. Please set Bunny.net or ImageKit environment variables.")
                
                github_image_urls = upload_files_to_storage(saved_files, "tours/images/")
                
                if github_image_urls:
                    logger.info(f"Successfully uploaded {len(github_image_urls)} images")
                    for i, url in enumerate(github_image_urls):
                        logger.info(f"  Uploaded URL {i+1}: {url}")
                    active_jobs[job_id]['current_step'] = f'Uploaded {len(github_image_urls)} images to cloud'
                    active_jobs[job_id]['progress'] = 50
                else:
                    error_msg = "Failed to upload images to ImageKit - check IMAGEKIT credentials"
                    logger.error(error_msg)
                    active_jobs[job_id]['current_step'] = error_msg
                    # Continue anyway - local video was created
                    
            except Exception as e:
                error_msg = f"Error uploading to ImageKit: {str(e)}"
                logger.error(error_msg)
                active_jobs[job_id]['current_step'] = error_msg
                github_image_urls = []
        
        if use_github_actions and github_image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Triggering GitHub Actions for high-quality rendering'
                active_jobs[job_id]['progress'] = 60
                
                logger.info(f"Triggering GitHub Actions with {len(github_image_urls)} images")
                
                # Build details string from property fields if available
                details_parts = []
                property_price = request.form.get('property_price', '').strip()
                property_beds = request.form.get('property_beds', '').strip()
                property_baths = request.form.get('property_baths', '').strip()
                property_sqft = request.form.get('property_sqft', '').strip()
                
                if property_price:
                    details_parts.append(property_price)
                if property_beds:
                    details_parts.append(f"{property_beds} Beds")
                if property_baths:
                    details_parts.append(f"{property_baths} Baths")
                if property_sqft:
                    details_parts.append(property_sqft)
                
                # Use composed details or fallback to details1
                property_details_string = ' | '.join(details_parts) if details_parts else details1
                
                logger.info(f"Triggering GitHub Actions for job {job_id} with {len(github_image_urls)} images")
                github_result = github_actions.trigger_video_render(
                        images=github_image_urls,
                        property_details={
                            'address': address,
                            'city': city,
                            'details': property_details_string,  # Remotion expects 'details' not 'details1'
                            'status': details2,  # Status is from details2
                            'agentName': agent_name,  # Remotion expects camelCase
                            'agentEmail': agent_email,
                            'agentPhone': agent_phone,
                            'brandName': brand_name
                        },
                        settings={
                            'durationPerImage': duration_per_image,
                            'effectSpeed': effect_speed,
                            'transitionDuration': transition_duration
                        }
                )
                
                logger.info(f"GitHub Actions trigger result: {github_result}")
                
                if github_result.get('success'):
                    active_jobs[job_id]['github_job_id'] = github_result['job_id']
                    active_jobs[job_id]['current_step'] = 'Starting Remotion rendering'
                    active_jobs[job_id]['progress'] = 70
                    logger.info(f"GitHub Actions job started successfully: {github_result['job_id']}")
                else:
                    error_detail = github_result.get('error', 'Unknown error')
                    error_details = github_result.get('details', '')
                    logger.error(f"Failed to start GitHub Actions: {error_detail}")
                    logger.error(f"Details: {error_details}")
                    active_jobs[job_id]['current_step'] = f"GitHub Actions failed: {error_detail}"
                    
                    # Provide helpful error message
                    if 'Unauthorized' in str(error_detail) or '401' in str(error_detail):
                        active_jobs[job_id]['current_step'] = "GitHub Actions failed - check GITHUB_TOKEN"
                    elif 'Not Found' in str(error_detail) or '404' in str(error_detail):
                        active_jobs[job_id]['current_step'] = "GitHub Actions failed - check GITHUB_OWNER and GITHUB_REPO"
                    
            except Exception as e:
                logger.error(f"Error with GitHub Actions: {e}")
                active_jobs[job_id]['current_step'] = f'GitHub Actions error: {str(e)}'
        
        # If watermark is requested, use local FFmpeg processing
        if watermark_id and 'saved_files' in locals() and saved_files:
            try:
                logger.info(f"Processing video with watermark {watermark_id} using local FFmpeg")
                active_jobs[job_id]['current_step'] = 'Adding watermark to video'
                active_jobs[job_id]['progress'] = 60
                
                # Import watermark-enabled video creation
                from ffmpeg_watermark_integration import create_ken_burns_video_with_watermark
                
                # Create output path
                output_filename = f"virtual_tour_{job_id}.mp4"
                output_path = os.path.join(TEMP_DIR, output_filename)
                
                # Create video with watermark
                created_video = create_ken_burns_video_with_watermark(
                    saved_files,
                    output_path,
                    duration_per_image,
                    watermark_id
                )
                
                if created_video and os.path.exists(created_video):
                    logger.info(f"Video with watermark created successfully: {created_video}")
                    active_jobs[job_id]['video_path'] = created_video
                    active_jobs[job_id]['video_available'] = True
                    active_jobs[job_id]['current_step'] = 'Video with watermark created'
                    active_jobs[job_id]['progress'] = 80
                    
                    # Upload to ImageKit for serving
                    try:
                        video_url = upload_video_to_storage(created_video, f"tours/videos/{output_filename}")
                        if video_url:
                            active_jobs[job_id]['video_url'] = video_url
                            logger.info(f"Video uploaded to ImageKit: {video_url}")
                    except Exception as e:
                        logger.error(f"Failed to upload video to ImageKit: {e}")
                        # Video still available locally
                        
            except Exception as e:
                logger.error(f"Error creating video with watermark: {e}")
                active_jobs[job_id]['current_step'] = f'Watermark processing failed: {str(e)}'
        
        # No other fallback - ImageKit is required for non-watermark videos
        
        # Create virtual tour HTML
        try:
            active_jobs[job_id]['current_step'] = 'Creating virtual tour viewer'
            active_jobs[job_id]['progress'] = 90
            
            # Generate HTML for virtual tour
            tour_html = generate_virtual_tour_html(job_id, active_jobs[job_id])
            tour_path = os.path.join(STORAGE_DIR, f"{job_id}_tour.html")
            
            with open(tour_path, 'w', encoding='utf-8') as f:
                f.write(tour_html)
            
            active_jobs[job_id]['virtual_tour_available'] = True
            active_jobs[job_id]['files_generated']['tour_html'] = tour_path
            logger.info(f"Virtual tour HTML created: {tour_path}")
            
        except Exception as e:
            logger.error(f"Error creating virtual tour HTML: {e}")
        
        # Finalize job
        processing_time = time.time() - start_time
        
        # If GitHub Actions was triggered, start polling for the video
        if active_jobs[job_id].get('github_job_id'):
            active_jobs[job_id]['status'] = 'processing'
            active_jobs[job_id]['progress'] = 75
            active_jobs[job_id]['current_step'] = 'Rendering high-quality video with Remotion'
            active_jobs[job_id]['processing_time'] = f"{processing_time:.2f} seconds"
            logger.info(f"Job {job_id} - GitHub Actions triggered, starting video polling")
            
            # Start background polling for GitHub Actions and ImageKit video
            github_job_id = active_jobs[job_id]['github_job_id']
            start_github_actions_polling(job_id, github_job_id)
        else:
            # Mark as completed even if GitHub Actions didn't run
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['current_step'] = 'Processing complete'
            active_jobs[job_id]['processing_time'] = f"{processing_time:.2f} seconds"
        
        return jsonify({
            'job_id': job_id,
            'status': active_jobs[job_id]['status'],  # Return actual status, not always 'completed'
            'video_available': active_jobs[job_id]['video_available'],
            'virtual_tour_available': active_jobs[job_id]['virtual_tour_available'],
            'video_available': active_jobs[job_id]['video_available'],
            'github_job_id': active_jobs[job_id].get('github_job_id'),
            'images_processed': active_jobs[job_id]['images_processed'],
            'processing_time': active_jobs[job_id]['processing_time'],
            'current_step': active_jobs[job_id].get('current_step', ''),
            'progress': active_jobs[job_id].get('progress', 100)
        })
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
        
        if job_id in active_jobs:
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = f'Error: {str(e)}'
        
        return jsonify({
            'error': str(e),
            'job_id': job_id
        }), 500

@virtual_tour_bp.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download the generated video"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        
        # Check if video is on ImageKit (GitHub Actions workflow)
        if job.get('imagekit_video') and job.get('files_generated', {}).get('imagekit_url'):
            imagekit_url = job['files_generated']['imagekit_url']
            # Redirect to ImageKit URL for download
            return redirect(imagekit_url)
        
        # Fallback: If we have a GitHub job ID but webhook hasn't updated yet
        if job.get('github_job_id'):
            github_job_id = job['github_job_id']
            # Use ImageKit for video URL
            imagekit_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT', 'https://ik.imagekit.io/brianosris/')
            if not imagekit_endpoint.endswith('/'):
                imagekit_endpoint += '/'
            video_url = f"{imagekit_endpoint}tours/videos/{github_job_id}.mp4"
            
            # Check if video exists on ImageKit
            try:
                import requests
                response = requests.head(video_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Video found on ImageKit for job {job_id}")
                    # Update job status  
                    job['imagekit_video'] = True
                    job['video_available'] = True
                    if 'files_generated' not in job:
                        job['files_generated'] = {}
                    job['files_generated']['cloudinary_url'] = video_url
                    # Redirect to the video
                    return redirect(video_url)
                else:
                    logger.info(f"Cloudinary URL not found (status {response.status_code}), will serve from Railway storage")
            except Exception as e:
                logger.info(f"Cloudinary check failed ({e}), will serve from Railway storage")
        
        if not job.get('video_available'):
            return jsonify({'error': 'Video not available'}), 404
        
        # Otherwise, serve local video file
        video_path = job['files_generated'].get('local_video')
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'virtual_tour_{job_id}.mp4'
        )
        
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@virtual_tour_bp.route('/view/<job_id>', methods=['GET'])
def view_tour(job_id):
    """View the virtual tour HTML"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        
        if not job.get('virtual_tour_available'):
            return jsonify({'error': 'Virtual tour not available'}), 404
        
        tour_path = job['files_generated'].get('tour_html')
        if not tour_path or not os.path.exists(tour_path):
            return jsonify({'error': 'Tour file not found'}), 404
        
        return send_file(tour_path, mimetype='text/html')
        
    except Exception as e:
        logger.error(f"Error viewing tour: {str(e)}")
        return jsonify({'error': str(e)}), 500

@virtual_tour_bp.route('/download/<job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """Download generated files"""
    try:
        # First check if this is a GitHub Actions job
        if job_id in active_jobs:
            job = active_jobs[job_id]
            
            # For video files from GitHub Actions
            if file_type in ['video', 'virtual_tour']:
                # First priority: Check for stored cloudinary URL
                if job.get('files_generated', {}).get('cloudinary_url'):
                    cloudinary_url = job['files_generated']['cloudinary_url']
                    # Add attachment flag to force download
                    if 'cloudinary.com' in cloudinary_url and '/upload/' in cloudinary_url:
                        cloudinary_url = cloudinary_url.replace('/upload/', '/upload/fl_attachment/')
                    logger.info(f"Using stored Cloudinary URL for job {job_id}: {cloudinary_url}")
                    return redirect(cloudinary_url)
                
                # Second priority: If we have a GitHub job ID, check if Cloudinary URL exists
                elif job.get('github_job_id'):
                    github_job_id = job['github_job_id']
                    # Use ImageKit for video URL with download parameter
                    imagekit_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT', 'https://ik.imagekit.io/brianosris/')
                    if not imagekit_endpoint.endswith('/'):
                        imagekit_endpoint += '/'
                    video_url = f"{imagekit_endpoint}tours/videos/{github_job_id}.mp4?dl=1"
                    
                    # Check if the ImageKit URL actually exists before redirecting
                    try:
                        import requests
                        check_url = video_url.replace('/fl_attachment/', '/')  # Check without attachment flag
                        response = requests.head(check_url, timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Cloudinary URL exists, redirecting for job {job_id}: {video_url}")
                            
                            # Update job data for future requests
                            job['cloudinary_video'] = True
                            job['video_available'] = True
                            if 'files_generated' not in job:
                                job['files_generated'] = {}
                            job['files_generated']['cloudinary_url'] = video_url
                            
                            return redirect(video_url)
                        else:
                            logger.info(f"Cloudinary URL not found (status {response.status_code}), will serve from Railway storage")
                    except Exception as e:
                        logger.info(f"Cloudinary check failed ({e}), will serve from Railway storage")
                    
                    # If we get here, Cloudinary doesn't have the video, so continue to serve from Railway
                
                elif job.get('status') == 'processing':
                    # For download requests, return error
                    return jsonify({
                        'error': 'Video is still being rendered',
                        'status': 'processing',
                        'progress': job.get('progress', 0),
                        'message': 'Please wait while your video is being generated.'
                    }), 202
                else:
                    # Video not available - return error
                    logger.warning(f"Video download failed for job {job_id}: status={job.get('status')}, github_job_id={job.get('github_job_id')}")
                    return jsonify({
                        'error': 'Video not available',
                        'status': job.get('status', 'unknown'),
                        'github_job_id': job.get('github_job_id'),
                        'message': 'The video generation may have failed or is not yet started.'
                    }), 404
            
            # For local files
            if job.get('files_generated', {}):
                if file_type == 'description' and 'description' in job['files_generated']:
                    filepath = job['files_generated']['description']
                    if os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True, download_name=f'property_description_{job_id}.txt')
                elif file_type == 'script' and 'script' in job['files_generated']:
                    filepath = job['files_generated']['script']
                    if os.path.exists(filepath):
                        return send_file(filepath, as_attachment=True, download_name=f'voiceover_script_{job_id}.txt')
        
        # Fallback to job directory lookup
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        if not os.path.exists(job_dir):
            # Try without job_ prefix
            job_dir = os.path.join(STORAGE_DIR, job_id)
            if not os.path.exists(job_dir):
                return jsonify({'error': 'Job not found'}), 404
        
        # Map file types to actual filenames
        file_mapping = {
            'video': f'virtual_tour_{job_id}.mp4',
            'virtual_tour': f'virtual_tour_{job_id}.mp4',
            'description': f'property_description_{job_id}.txt',
            'script': f'voiceover_script_{job_id}.txt'
        }
        
        if file_type not in file_mapping:
            return jsonify({'error': 'Invalid file type'}), 400
        
        filepath = os.path.join(job_dir, file_mapping[file_type])
        
        if os.path.exists(filepath):
            return send_file(
                filepath, 
                as_attachment=True,
                download_name=os.path.basename(filepath)
            )
        else:
            return jsonify({'error': f'File not found: {file_type}'}), 404
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': str(e)}), 500

@virtual_tour_bp.route('/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get status of a specific job"""
    if job_id not in active_jobs:
        # Check if job directory exists
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        if os.path.exists(job_dir):
            # Job exists but not in memory (server restarted)
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'message': 'Job completed (retrieved from storage)'
            })
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    # REMOVED GitHub API status checking to prevent rate limit exhaustion
    # The Cloudinary polling thread already handles checking for video completion
    # Each status check was making an API call, causing 30+ calls per minute
    
    # Fallback: Check if video exists on ImageKit directly
    if job.get('github_job_id') and job.get('status') != 'completed':
        imagekit_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT', 'https://ik.imagekit.io/brianosris/')
        if not imagekit_endpoint.endswith('/'):
            imagekit_endpoint += '/'
        video_url = f"{imagekit_endpoint}tours/videos/{job['github_job_id']}.mp4"
        
        # Simple HEAD request to check if video exists
        try:
            import requests
            response = requests.head(video_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Video found on Cloudinary for job {job_id}")
                job['cloudinary_video'] = True
                job['files_generated']['cloudinary_url'] = video_url
                job['status'] = 'completed'
                job['progress'] = 100
                job['current_step'] = 'Video ready for download'
        except Exception as e:
            logger.debug(f"Video not ready yet for job {job_id}: {e}")
    
    # Build response data
    response_data = {
        'job_id': job_id,
        'status': job.get('status', 'unknown'),
        'progress': job.get('progress', 0),
        'current_step': job.get('current_step', ''),
        'video_available': job.get('video_available', False),
        'virtual_tour_available': job.get('virtual_tour_available', False),
        'images_processed': job.get('images_processed', 0),
        'processing_time': job.get('processing_time', ''),
        'error': job.get('error', None),
        'github_job_id': job.get('github_job_id', None),
        'files_generated': job.get('files_generated', {})
    }
    
    # Add video URL if available from multiple sources
    if job.get('files_generated', {}).get('cloudinary_url'):
        response_data['video_url'] = job['files_generated']['cloudinary_url']
    elif job.get('github_job_id'):
        # Always construct URL if we have a GitHub job ID, regardless of status
        github_job_id = job['github_job_id']
        imagekit_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT', 'https://ik.imagekit.io/brianosris/')
        if not imagekit_endpoint.endswith('/'):
            imagekit_endpoint += '/'
        video_url = f"{imagekit_endpoint}tours/videos/{github_job_id}.mp4"
        response_data['video_url'] = video_url
        # Also update the files_generated for consistency
        response_data['files_generated']['cloudinary_url'] = video_url
        logger.info(f"Constructed video URL for job {job_id}: {video_url}")
    
    return jsonify(response_data)

def generate_virtual_tour_html(job_id, job_data):
    """Generate HTML for virtual tour viewer"""
    video_url = ""
    
    # Prefer ImageKit URL, then local video
    if job_data.get('imagekit_video') and 'imagekit_url' in job_data['files_generated']:
        video_url = job_data['files_generated']['imagekit_url']
    elif job_data.get('video_available'):
        video_url = f"/api/virtual-tour/download/{job_id}"
    
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Tour - Job {job_id}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }}
        .container {{
            width: 100%;
            max-width: 1200px;
            padding: 20px;
        }}
        .video-wrapper {{
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
            background-color: #000;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        video {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }}
        .info {{
            margin-top: 20px;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 8px;
            color: #333;
        }}
        .info h2 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .info p {{
            margin: 10px 0;
        }}
        .no-video {{
            text-align: center;
            color: #fff;
            padding: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="video-wrapper">
            {video_content}
        </div>
        <div class="info">
            <h2>Virtual Tour Information</h2>
            <p><strong>Job ID:</strong> {job_id}</p>
            <p><strong>Status:</strong> {status}</p>
            <p><strong>Images Processed:</strong> {images_processed}</p>
            <p><strong>Processing Time:</strong> {processing_time}</p>
            {github_info}
        </div>
    </div>
</body>
</html>'''
    
    if video_url:
        video_content = f'<video controls autoplay loop muted><source src="{video_url}" type="video/mp4">Your browser does not support the video tag.</video>'
    else:
        video_content = '<div class="no-video"><h3>Video is being processed...</h3><p>Please refresh this page in a few moments.</p></div>'
    
    github_info = ""
    if job_data.get('github_job_id'):
        github_info = f'<p><strong>GitHub Actions Job:</strong> {job_data["github_job_id"]}</p>'
    
    return html_template.format(
        job_id=job_id,
        video_content=video_content,
        status=job_data.get('status', 'Unknown'),
        images_processed=job_data.get('images_processed', 0),
        processing_time=job_data.get('processing_time', 'N/A'),
        github_info=github_info
    )