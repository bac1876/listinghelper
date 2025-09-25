from flask import Blueprint, request, jsonify, send_file
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
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ffmpeg_ken_burns import create_ken_burns_video
from cloudinary_integration import generate_cloudinary_video
try:
    from creatomate_integration_v2 import create_real_estate_video
    CREATOMATE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Creatomate integration not available: {e}")
    CREATOMATE_AVAILABLE = False

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# Railway storage directory
STORAGE_DIR = '/app/storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory job tracking with detailed status
active_jobs = {}

ROOM_LABELS = {
    'front': 'Front',
    'primary_bedroom': 'Primary Bedroom',
    'bedroom_1': 'Bedroom 1',
    'bedroom_2': 'Bedroom 2',
    'bedroom_3': 'Bedroom 3',
    'bedroom_4': 'Bedroom 4',
    'bedroom_5': 'Bedroom 5',
    'primary_bath': 'Primary Bath',
    'bath_1': 'Bath 1',
    'bath_2': 'Bath 2',
    'bath_3': 'Bath 3',
    'kitchen': 'Kitchen',
    'living_room': 'Living Room',
    'dining_room': 'Dining Room',
    'garage': 'Garage',
    'back_yard': 'Back Yard',
    'other': 'Other'
}


def format_room_label(room_value: str, other_label: str = "") -> str:
    if not room_value:
        return 'Unassigned'
    if room_value == 'other':
        return other_label.strip() or 'Other'
    return ROOM_LABELS.get(room_value, room_value)


def generate_room_scripts(assignments, property_details):
    scripts = []
    if not assignments:
        return scripts

    address = property_details.get('address', '').split('\n')[0]
    for idx, item in enumerate(assignments, start=1):
        room_label = format_room_label(item.get('room'), item.get('other_label'))
        description_hint = property_details.get('details1', '')
        narrative = (
            f"Scene {idx}: Highlight the {room_label.lower()}"
            f"{' at ' + address if address else ''}."
        )
        if description_hint:
            narrative += f" Emphasize {description_hint}."
        scripts.append(narrative)

    return scripts

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

@virtual_tour_bp.route('/health', methods=['GET'])
def health_check():
    """Check if FFmpeg is available and test basic functionality"""
    health_status = {
        'status': 'healthy',
        'ffmpeg_available': False,
        'ffmpeg_version': None,
        'ffmpeg_test_passed': False,
        'storage_writable': False,
        'storage_path': STORAGE_DIR,
        'ffmpeg_binary': None
    }
    
    # Check FFmpeg - try imageio-ffmpeg first
    ffmpeg_cmd = 'ffmpeg'
    try:
        import imageio_ffmpeg as ffmpeg
        ffmpeg_cmd = ffmpeg.get_ffmpeg_exe()
        health_status['ffmpeg_binary'] = 'imageio-ffmpeg'
    except:
        health_status['ffmpeg_binary'] = 'system'
    
    try:
        result = subprocess.run([ffmpeg_cmd, '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            health_status['ffmpeg_available'] = True
            health_status['ffmpeg_version'] = result.stdout.split('\\n')[0]
    except:
        pass
    
    # Check storage
    try:
        test_file = os.path.join(STORAGE_DIR, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        health_status['storage_writable'] = True
    except:
        pass
    
    return jsonify(health_status)

@virtual_tour_bp.route('/upload', methods=['POST'])
def upload_images():
    """Handle image upload and create virtual tour"""
    job_id = str(uuid.uuid4())
    start_time = time.time()
    
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
                    'cloudinary_video': job.get('cloudinary_video', False),
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
            'cloudinary_video': False,
            'images_processed': 0,
            'files_generated': {},
            'room_assignments': []
        }
        
        def update_job_progress(job_id, status, step, progress):
            if job_id in active_jobs:
                active_jobs[job_id].update({
                    'status': status,
                    'current_step': step,
                    'progress': progress
                })
        
        # Get quality preference from form data
        quality_preference = request.form.get('quality', None)
        if quality_preference and quality_preference not in ['deployment', 'medium', 'high', 'premium']:
            quality_preference = None  # Invalid quality, use auto-detection
        
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
        
        # Get property details if provided
        property_details = {
            'address': request.form.get('address', 'Beautiful Property\nYour City, State'),
            'details1': request.form.get('details1', '2,500 sqft\n3 Bedrooms\n2 Bathrooms'),
            'details2': request.form.get('details2', 'Modern Home\nMove-in Ready\nCall for Price'),
            'agent_name': request.form.get('agent_name', 'Your Real Estate Agent'),
            'agent_email': request.form.get('agent_email', 'agent@realestate.com'),
            'agent_phone': request.form.get('agent_phone', '(555) 123-4567'),
            'brand_name': request.form.get('brand_name', 'Premium Real Estate'),
            'agent_photo': request.form.get('agent_photo', '')
        }
        
        # Get uploaded files
        if 'files' not in request.files:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['error'] = 'No files uploaded'
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files:
            active_jobs[job_id]['status'] = 'failed'
            active_jobs[job_id]['error'] = 'No files selected'
            return jsonify({'error': 'No files selected'}), 400

        room_assignment_payload = []
        raw_assignments = request.form.get('room_assignments')
        if raw_assignments:
            try:
                parsed = json.loads(raw_assignments)
                if isinstance(parsed, list):
                    room_assignment_payload = parsed
            except json.JSONDecodeError:
                logger.warning('Invalid room_assignments payload; ignoring')
        
        # Create job directory
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        os.makedirs(job_dir, exist_ok=True)
        
        # Save uploaded images
        logger.info(f"Processing {len(files)} images for job {job_id}")
        update_job_progress(job_id, 'processing', 'uploading_images', 10)
        
        saved_paths = []
        for i, file in enumerate(files):
            if file and file.filename:
                # Secure filename
                filename = f"{i:03d}_{file.filename}"
                filepath = os.path.join(job_dir, filename)
                file.save(filepath)
                saved_paths.append(filepath)
                logger.info(f"Saved: {filename}")

                assignment_info = room_assignment_payload[i] if i < len(room_assignment_payload) else {}
                room_value = (assignment_info.get('room') or '').strip()
                other_label = (assignment_info.get('other_label') or '').strip()
                display_name = assignment_info.get('filename') or file.filename
                active_jobs[job_id]['room_assignments'].append({
                    'file_id': assignment_info.get('file_id'),
                    'filename': file.filename,
                    'display_name': display_name,
                    'saved_filename': filename,
                    'room': room_value,
                    'other_label': other_label,
                    'room_label': format_room_label(room_value, other_label)
                })

        active_jobs[job_id]['images_processed'] = len(saved_paths)
        active_jobs[job_id]['files_generated']['image_count'] = len(saved_paths)
        active_jobs[job_id]['files_generated']['room_assignments'] = active_jobs[job_id]['room_assignments']
        active_jobs[job_id]['files_generated']['room_scripts'] = generate_room_scripts(
            active_jobs[job_id]['room_assignments'],
            property_details
        )
        
        # Optimize images
        logger.info("Optimizing images...")
        update_job_progress(job_id, 'processing', 'optimizing_images', 20)
        
        from PIL import Image
        optimized_paths = []
        for i, path in enumerate(saved_paths):
            try:
                with Image.open(path) as img:
                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    # Resize if too large
                    max_size = (1920, 1080)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # Save optimized version
                    opt_path = os.path.join(job_dir, f'opt_{i:03d}.jpg')
                    img.save(opt_path, 'JPEG', quality=90, optimize=True)
                    optimized_paths.append(opt_path)
            except Exception as e:
                logger.error(f"Error optimizing image {path}: {e}")
                optimized_paths.append(path)  # Use original if optimization fails
        
        # Create Ken Burns MP4 video
        try:
            # Check if we should use Creatomate
            use_creatomate = os.environ.get('USE_CREATOMATE', 'false').lower() == 'true' and CREATOMATE_AVAILABLE
            
            if use_creatomate:
                logger.info("Using Creatomate for professional video generation...")
                update_job_progress(job_id, 'processing', 'creating_professional_video', 30)
                
                # Use Creatomate API
                video_url = create_real_estate_video(
                    optimized_paths,
                    property_details,
                    job_id
                )
                
                if video_url:
                    # Download the video from Creatomate
                    video_path = os.path.join(job_dir, f'virtual_tour_{job_id}.mp4')
                    try:
                        import requests
                        response = requests.get(video_url, stream=True)
                        response.raise_for_status()
                        
                        with open(video_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        created_video_path = video_path
                        logger.info(f"Downloaded Creatomate video to {video_path}")
                    except Exception as e:
                        logger.error(f"Error downloading Creatomate video: {e}")
                        created_video_path = None
                else:
                    created_video_path = None
            else:
                logger.info("Creating Ken Burns MP4 video...")
                update_job_progress(job_id, 'processing', 'creating_video', 30)
                
                # Create the professional Ken Burns video with optional watermark
                video_path = os.path.join(job_dir, f'virtual_tour_{job_id}.mp4')
                
                # Use watermark-enabled function if watermark is specified
                if watermark_id:
                    try:
                        from ffmpeg_watermark_integration import create_ken_burns_video_with_watermark
                        logger.info(f"Creating video with watermark: {watermark_id}")
                        update_job_progress(job_id, 'processing', 'adding_watermark', 35)
                        created_video_path = create_ken_burns_video_with_watermark(
                            optimized_paths, 
                            video_path, 
                            job_id,
                            watermark_id=watermark_id,
                            quality=quality_preference
                        )
                    except Exception as watermark_error:
                        logger.error(f"Error with watermark, falling back to regular video: {watermark_error}")
                        # Fallback to regular video creation
                        created_video_path = create_ken_burns_video(
                            optimized_paths, 
                            video_path, 
                            job_id,
                            quality=quality_preference
                        )
                else:
                    # Regular video creation without watermark
                    created_video_path = create_ken_burns_video(
                        optimized_paths, 
                        video_path, 
                        job_id,
                        quality=quality_preference
                    )
            
            if os.path.exists(created_video_path):
                active_jobs[job_id]['video_available'] = True
                active_jobs[job_id]['files_generated']['video'] = os.path.basename(created_video_path)
                logger.info(f"Ken Burns video created: {created_video_path}")
                update_job_progress(job_id, 'processing', 'video_complete', 50)
            
        except Exception as e:
            logger.error(f"Error creating Ken Burns video: {e}")
            active_jobs[job_id]['error'] = f"Video generation failed: {str(e)}"
        
        # Try Cloudinary video generation
        try:
            logger.info("Attempting Cloudinary video generation...")
            update_job_progress(job_id, 'processing', 'generating_cloud_video', 60)
            
            cloudinary_result = generate_cloudinary_video(optimized_paths, job_id)
            
            if cloudinary_result and cloudinary_result.get('success'):
                active_jobs[job_id]['cloudinary_video'] = True
                active_jobs[job_id]['files_generated']['cloud_video_url'] = cloudinary_result['video_url']
                active_jobs[job_id]['files_generated']['cloud_video_download'] = cloudinary_result['download_url']
                logger.info(f"Cloudinary video created: {cloudinary_result['video_url']}")
                update_job_progress(job_id, 'processing', 'cloud_video_complete', 70)
            
        except Exception as e:
            logger.error(f"Cloudinary video generation failed: {e}")
        
        # Generate property description
        try:
            logger.info("Generating property description...")
            update_job_progress(job_id, 'processing', 'generating_description', 80)
            
            description = generate_property_description(len(saved_paths))
            desc_path = os.path.join(job_dir, f'property_description_{job_id}.txt')
            with open(desc_path, 'w') as f:
                f.write(description)
            active_jobs[job_id]['files_generated']['description'] = os.path.basename(desc_path)
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
        
        # Generate voiceover script
        try:
            logger.info("Generating voiceover script...")
            update_job_progress(job_id, 'processing', 'generating_script', 90)
            
            script = generate_voiceover_script(len(saved_paths))
            script_path = os.path.join(job_dir, f'voiceover_script_{job_id}.txt')
            with open(script_path, 'w') as f:
                f.write(script)
            active_jobs[job_id]['files_generated']['script'] = os.path.basename(script_path)
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
        
        # Mark job as completed
        processing_time = time.time() - start_time
        active_jobs[job_id].update({
            'status': 'completed',
            'progress': 100,
            'current_step': 'completed',
            'processing_time': f"{processing_time:.1f} seconds"
        })
        
        logger.info(f"Job {job_id} completed in {processing_time:.1f} seconds")
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'video_available': active_jobs[job_id]['video_available'],
            'virtual_tour_available': active_jobs[job_id]['video_available'],  # For backward compatibility
            'cloudinary_video': active_jobs[job_id]['cloudinary_video'],
            'images_processed': len(saved_paths),
            'processing_time': f"{processing_time:.1f} seconds",
            'files_generated': active_jobs[job_id]['files_generated']
        })
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        if job_id in active_jobs:
            active_jobs[job_id].update({
                'status': 'failed',
                'error': str(e)
            })
        return jsonify({'error': str(e)}), 500

def generate_property_description(num_images):
    """Generate a professional property description"""
    return f"""STUNNING LUXURY PROPERTY - VIRTUAL TOUR

Experience this exceptional property through our professional virtual tour featuring {num_images} carefully selected views.

PROPERTY HIGHLIGHTS:
• Meticulously maintained and presented
• Thoughtfully designed living spaces
• Premium finishes throughout
• Abundant natural light
• Professional photography showcasing every detail

This virtual tour captures the essence and elegance of this remarkable property. Each image has been professionally captured to highlight the unique features and characteristics that make this home truly special.

For more information or to schedule a private showing, please contact your real estate professional.

Virtual Tour Created: {datetime.now().strftime('%B %d, %Y')}
"""

def generate_voiceover_script(num_images):
    """Generate a voiceover script for the virtual tour"""
    return f"""VIRTUAL TOUR VOICEOVER SCRIPT

[Opening - Soft, welcoming tone]

Welcome to this exceptional property virtual tour. Over the next few moments, we'll take you through {num_images} stunning views of this remarkable home.

[Transition between images - maintain warm, professional tone]

As we move through each space, notice the attention to detail... the quality of finishes... and the thoughtful design that makes this property truly special.

[For each image, you might say variations of:]

• "Here we see the stunning [room/feature], showcasing [specific detail]..."
• "Notice the beautiful [architectural element] that adds character to this space..."
• "The [natural light/open concept/premium finishes] create an inviting atmosphere..."
• "This view highlights the [specific feature] that sets this property apart..."

[Closing - Inviting, professional tone]

Thank you for taking this virtual tour with us today. This property offers an exceptional opportunity for discerning buyers. To experience these stunning spaces in person, please contact your real estate professional to arrange a private showing.

[End]

Note: This script can be customized based on the specific features visible in each image. Consider adding specific details about rooms, architectural features, or unique selling points as they appear in the tour.
"""

# Removed HTML slideshow function - we only generate MP4 videos

@virtual_tour_bp.route('/download/<job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """Download generated files"""
    try:
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        
        if not os.path.exists(job_dir):
            return jsonify({'error': 'Job not found'}), 404
        
        # Map file types to actual filenames
        file_mapping = {
            'video': f'virtual_tour_{job_id}.mp4',
            'virtual_tour': f'virtual_tour_{job_id}.mp4',  # For backward compatibility
            'description': f'property_description_{job_id}.txt',
            'script': f'voiceover_script_{job_id}.txt'
        }
        
        if file_type not in file_mapping:
            return jsonify({'error': 'Invalid file type'}), 400
        
        filepath = os.path.join(job_dir, file_mapping[file_type])
        
        # No HTML slideshow generation - only MP4 videos
        
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

@virtual_tour_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all active jobs"""
    jobs_list = []
    for job_id, job_data in active_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'status': job_data.get('status', 'unknown'),
            'progress': job_data.get('progress', 0),
            'current_step': job_data.get('current_step', ''),
            'video_available': job_data.get('video_available', False),
            'virtual_tour_available': job_data.get('virtual_tour_available', False),
            'images_processed': job_data.get('images_processed', 0)
        })
    
    return jsonify({
        'jobs': jobs_list,
        'total': len(jobs_list)
    })

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
    return jsonify({
        'job_id': job_id,
        'status': job.get('status', 'unknown'),
        'progress': job.get('progress', 0),
        'current_step': job.get('current_step', ''),
        'video_available': job.get('video_available', False),
        'virtual_tour_available': job.get('virtual_tour_available', False),
        'cloudinary_video': job.get('cloudinary_video', False),
        'images_processed': job.get('images_processed', 0),
        'processing_time': job.get('processing_time', ''),
        'error': job.get('error', None)
    })
