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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ffmpeg_ken_burns import create_ken_burns_video
from cloudinary_integration import generate_cloudinary_video
from github_actions_integration import GitHubActionsIntegration
from upload_to_cloudinary import upload_files_to_cloudinary

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# Railway storage directory
STORAGE_DIR = '/app/storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory job tracking with detailed status
active_jobs = {}

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
        'ffmpeg_binary': None,
        'github_actions_available': github_actions is not None
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
            health_status['ffmpeg_version'] = result.stdout.split('\n')[0]
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
    
    # Check GitHub Actions
    if github_actions:
        try:
            workflow_status = github_actions.get_workflow_status()
            health_status['github_workflow_status'] = workflow_status
        except:
            pass
    
    return jsonify(health_status)

@virtual_tour_bp.route('/check-github-job/<job_id>', methods=['GET'])
def check_github_job(job_id):
    """Check the status of a GitHub Actions video render job"""
    if not github_actions:
        return jsonify({
            'success': False,
            'error': 'GitHub Actions not configured'
        }), 503
    
    try:
        result = github_actions.check_job_status(job_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error checking GitHub job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
        
        # Process uploaded files if any
        if 'files' in request.files:
            files = request.files.getlist('files')
            logger.info(f"Received {len(files)} files for job {job_id}")
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
            
            # Save uploaded files
            saved_files = []
            for i, file in enumerate(files):
                if file and file.filename:
                    filename = f"image_{i}_{file.filename}"
                    filepath = os.path.join(job_dir, filename)
                    file.save(filepath)
                    saved_files.append(filepath)
                    logger.info(f"Saved file: {filename}")
            
            # Update job progress
            active_jobs[job_id]['images_processed'] = len(saved_files)
            active_jobs[job_id]['current_step'] = f'Saved {len(saved_files)} images'
            active_jobs[job_id]['progress'] = 10
            
            # Create local video with FFmpeg
            if saved_files:
                try:
                    active_jobs[job_id]['current_step'] = 'Creating video with Ken Burns effects'
                    active_jobs[job_id]['progress'] = 20
                    
                    output_path = os.path.join(job_dir, 'virtual_tour.mp4')
                    success = create_ken_burns_video(
                        saved_files, 
                        output_path,
                        duration_per_image=duration_per_image,
                        effect_speed=effect_speed,
                        transition_duration=transition_duration,
                        property_details={
                            'address': address,
                            'city': city,
                            'details1': details1,
                            'details2': details2,
                            'agent_name': agent_name,
                            'agent_email': agent_email,
                            'agent_phone': agent_phone,
                            'brand_name': brand_name
                        }
                    )
                    
                    if success and os.path.exists(output_path):
                        active_jobs[job_id]['video_available'] = True
                        active_jobs[job_id]['files_generated']['local_video'] = output_path
                        active_jobs[job_id]['progress'] = 50
                        logger.info(f"Video created successfully: {output_path}")
                except Exception as e:
                    logger.error(f"Error creating video: {e}")
                    active_jobs[job_id]['current_step'] = f'Error creating video: {str(e)}'
        
        # Check if we should use GitHub Actions for high-quality rendering
        use_github_actions = os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() == 'true' and github_actions
        
        # Prepare image URLs for GitHub Actions
        github_image_urls = image_urls or []
        
        # If we have uploaded files but no URLs, upload them to Cloudinary first
        if use_github_actions and 'saved_files' in locals() and saved_files and not image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Uploading images to Cloudinary for GitHub Actions'
                active_jobs[job_id]['progress'] = 40
                
                # Upload files to Cloudinary
                logger.info(f"Uploading {len(saved_files)} files to Cloudinary...")
                for i, file in enumerate(saved_files):
                    logger.info(f"  Will upload file {i+1}: {os.path.basename(file)}")
                
                github_image_urls = upload_files_to_cloudinary(saved_files)
                
                if github_image_urls:
                    logger.info(f"Successfully uploaded {len(github_image_urls)} images to Cloudinary")
                    for i, url in enumerate(github_image_urls):
                        logger.info(f"  Uploaded URL {i+1}: {url}")
                    active_jobs[job_id]['current_step'] = f'Uploaded {len(github_image_urls)} images to cloud'
                    active_jobs[job_id]['progress'] = 50
                else:
                    logger.error("Failed to upload images to Cloudinary")
                    
            except Exception as e:
                logger.error(f"Error uploading to Cloudinary: {e}")
                github_image_urls = []
        
        if use_github_actions and github_image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Triggering GitHub Actions for high-quality rendering'
                active_jobs[job_id]['progress'] = 60
                
                if github_image_urls:
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
                    
                    if github_result.get('success'):
                        active_jobs[job_id]['github_job_id'] = github_result['job_id']
                        active_jobs[job_id]['current_step'] = 'GitHub Actions rendering started'
                        active_jobs[job_id]['progress'] = 70
                        logger.info(f"GitHub Actions job started: {github_result['job_id']}")
                    else:
                        logger.error(f"Failed to start GitHub Actions: {github_result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error with GitHub Actions: {e}")
                active_jobs[job_id]['current_step'] = f'GitHub Actions error: {str(e)}'
        
        # Use Cloudinary as fallback
        elif image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Creating video with Cloudinary'
                active_jobs[job_id]['progress'] = 60
                
                cloudinary_result = generate_cloudinary_video(
                    image_urls,
                    property_details={
                        'address': address,
                        'city': city,
                        'details1': details1,
                        'details2': details2,
                        'agent_name': agent_name,
                        'agent_email': agent_email,
                        'agent_phone': agent_phone,
                        'brand_name': brand_name
                    }
                )
                
                if cloudinary_result.get('success'):
                    active_jobs[job_id]['cloudinary_video'] = True
                    active_jobs[job_id]['files_generated']['cloudinary_url'] = cloudinary_result['url']
                    active_jobs[job_id]['progress'] = 80
                    logger.info(f"Cloudinary video created: {cloudinary_result['url']}")
                    
            except Exception as e:
                logger.error(f"Error with Cloudinary: {e}")
                active_jobs[job_id]['current_step'] = f'Cloudinary error: {str(e)}'
        
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
        
        # If GitHub Actions was triggered, don't mark as completed yet
        if active_jobs[job_id].get('github_job_id'):
            active_jobs[job_id]['status'] = 'processing'
            active_jobs[job_id]['progress'] = 75
            active_jobs[job_id]['current_step'] = 'GitHub Actions rendering in progress'
            active_jobs[job_id]['processing_time'] = f"{processing_time:.2f} seconds"
            logger.info(f"Job {job_id} waiting for GitHub Actions to complete")
        else:
            # Only mark as completed if no GitHub Actions
            active_jobs[job_id]['status'] = 'completed'
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['current_step'] = 'Processing complete'
            active_jobs[job_id]['processing_time'] = f"{processing_time:.2f} seconds"
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'video_available': active_jobs[job_id]['video_available'],
            'virtual_tour_available': active_jobs[job_id]['virtual_tour_available'],
            'cloudinary_video': active_jobs[job_id]['cloudinary_video'],
            'github_job_id': active_jobs[job_id].get('github_job_id'),
            'images_processed': active_jobs[job_id]['images_processed'],
            'processing_time': active_jobs[job_id]['processing_time']
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
        
        # Check if video is on Cloudinary (GitHub Actions workflow)
        if job.get('cloudinary_video') and job.get('files_generated', {}).get('cloudinary_url'):
            cloudinary_url = job['files_generated']['cloudinary_url']
            # Redirect to Cloudinary URL for download
            return redirect(cloudinary_url)
        
        # Fallback: If we have a GitHub job ID but webhook hasn't updated yet
        if job.get('github_job_id'):
            github_job_id = job['github_job_id']
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dib3kbifc')
            video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{github_job_id}.mp4"
            
            # Check if video exists on Cloudinary
            try:
                import requests
                response = requests.head(video_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Video found on Cloudinary (fallback) for job {job_id}")
                    # Update job status
                    job['cloudinary_video'] = True
                    job['video_available'] = True
                    if 'files_generated' not in job:
                        job['files_generated'] = {}
                    job['files_generated']['cloudinary_url'] = video_url
                    # Redirect to the video
                    return redirect(video_url)
            except Exception as e:
                logger.debug(f"Cloudinary check failed: {e}")
        
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
                # Check if video is available and has cloudinary URL
                if job.get('video_available') and job.get('cloudinary_video') and job.get('files_generated', {}).get('cloudinary_url'):
                    cloudinary_url = job['files_generated']['cloudinary_url']
                    # Redirect to Cloudinary URL
                    return redirect(cloudinary_url)
                
                # Fallback: If we have a GitHub job ID but webhook hasn't updated yet, check Cloudinary directly
                elif job.get('github_job_id'):
                    github_job_id = job['github_job_id']
                    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dib3kbifc')
                    video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{github_job_id}.mp4"
                    
                    # Check if video exists on Cloudinary
                    try:
                        import requests
                        response = requests.head(video_url, timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Video found on Cloudinary (fallback) for job {job_id}")
                            # Update job status since webhook didn't
                            job['cloudinary_video'] = True
                            job['video_available'] = True
                            if 'files_generated' not in job:
                                job['files_generated'] = {}
                            job['files_generated']['cloudinary_url'] = video_url
                            job['status'] = 'completed'
                            job['progress'] = 100
                            # Redirect to the video
                            return redirect(video_url)
                    except Exception as e:
                        logger.debug(f"Cloudinary check failed for job {job_id}: {e}")
                
                elif job.get('status') == 'processing':
                    return jsonify({
                        'error': 'Video is still being rendered',
                        'status': 'processing',
                        'progress': job.get('progress', 0),
                        'message': 'Please wait while your video is being generated. This may take 1-2 minutes.'
                    }), 202  # 202 Accepted - request accepted but processing not complete
                else:
                    return jsonify({
                        'error': 'Video not available',
                        'status': job.get('status', 'unknown'),
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
    
    # Check GitHub Actions status if applicable
    if job.get('github_job_id') and github_actions:
        try:
            github_status = github_actions.check_job_status(job['github_job_id'])
            if github_status.get('status') == 'completed' and github_status.get('video_url'):
                job['cloudinary_video'] = True
                job['files_generated']['cloudinary_url'] = github_status['video_url']
                job['status'] = 'completed'
                job['progress'] = 100
        except Exception as e:
            logger.error(f"Error checking GitHub job status: {e}")
    
    # Fallback: Check if video exists on Cloudinary directly
    if job.get('github_job_id') and job.get('status') != 'completed':
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dib3kbifc')
        video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{job['github_job_id']}.mp4"
        
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
        'cloudinary_video': job.get('cloudinary_video', False),
        'images_processed': job.get('images_processed', 0),
        'processing_time': job.get('processing_time', ''),
        'error': job.get('error', None),
        'github_job_id': job.get('github_job_id', None)
    }
    
    # Add video URL if we have a GitHub job ID and status is completed
    if job.get('github_job_id') and job.get('status') == 'completed':
        github_job_id = job['github_job_id']
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', 'dib3kbifc')
        video_url = f"https://res.cloudinary.com/{cloud_name}/video/upload/tours/{github_job_id}.mp4"
        response_data['video_url'] = video_url
        # Also update the files_generated for consistency
        if 'files_generated' not in response_data:
            response_data['files_generated'] = {}
        response_data['files_generated']['cloudinary_url'] = video_url
    
    return jsonify(response_data)

def generate_virtual_tour_html(job_id, job_data):
    """Generate HTML for virtual tour viewer"""
    video_url = ""
    
    # Prefer Cloudinary URL, then local video
    if job_data.get('cloudinary_video') and 'cloudinary_url' in job_data['files_generated']:
        video_url = job_data['files_generated']['cloudinary_url']
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