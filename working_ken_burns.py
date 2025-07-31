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
from css3_ken_burns import create_css3_ken_burns_slideshow
from cloudinary_integration import generate_cloudinary_video

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# Railway storage directory
STORAGE_DIR = '/app/storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory job tracking with detailed status
active_jobs = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        'storage_path': STORAGE_DIR
    }
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
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
            'files_generated': {}
        }
        
        def update_job_progress(job_id, status, step, progress):
            if job_id in active_jobs:
                active_jobs[job_id].update({
                    'status': status,
                    'current_step': step,
                    'progress': progress
                })
        
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
        
        active_jobs[job_id]['images_processed'] = len(saved_paths)
        
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
        
        # Create CSS3 Ken Burns virtual tour
        try:
            logger.info("Creating CSS3 Ken Burns virtual tour...")
            update_job_progress(job_id, 'processing', 'creating_virtual_tour', 30)
            
            # Create the professional CSS3 virtual tour
            virtual_tour_path = create_css3_ken_burns_slideshow(
                optimized_paths, 
                job_dir, 
                job_id,
                title="Luxury Property Showcase"
            )
            
            if os.path.exists(virtual_tour_path):
                active_jobs[job_id]['virtual_tour_available'] = True
                active_jobs[job_id]['files_generated']['virtual_tour'] = os.path.basename(virtual_tour_path)
                logger.info(f"CSS3 virtual tour created: {virtual_tour_path}")
                update_job_progress(job_id, 'processing', 'virtual_tour_complete', 50)
            
        except Exception as e:
            logger.error(f"Error creating CSS3 virtual tour: {e}")
        
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
            'virtual_tour_available': active_jobs[job_id]['virtual_tour_available'],
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

def create_html_slideshow(images, job_id):
    """Create a simple HTML slideshow as fallback"""
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Virtual Tour - Job {job_id}</title>
    <style>
        body {{ margin: 0; padding: 0; background: #000; overflow: hidden; }}
        .slideshow {{ position: relative; width: 100vw; height: 100vh; }}
        .slide {{ position: absolute; width: 100%; height: 100%; display: none; }}
        .slide img {{ width: 100%; height: 100%; object-fit: contain; }}
        .slide.active {{ display: block; animation: fadeIn 1s; }}
        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        .controls {{ position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); }}
        .controls button {{ margin: 0 10px; padding: 10px 20px; }}
    </style>
</head>
<body>
    <div class="slideshow">
        {"".join([f'<div class="slide {"active" if i == 0 else ""}"><img src="data:image/jpeg;base64,{img}" alt="Slide {i+1}"></div>' for i, img in enumerate(images)])}
    </div>
    <div class="controls">
        <button onclick="previousSlide()">Previous</button>
        <button onclick="nextSlide()">Next</button>
        <button onclick="toggleFullscreen()">Fullscreen</button>
    </div>
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        
        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].classList.add('active');
        }}
        
        function nextSlide() {{ showSlide(currentSlide + 1); }}
        function previousSlide() {{ showSlide(currentSlide - 1); }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        // Auto-advance slides
        setInterval(nextSlide, 5000);
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') nextSlide();
            if (e.key === 'ArrowLeft') previousSlide();
            if (e.key === 'f') toggleFullscreen();
        }});
    </script>
</body>
</html>"""
    
    slideshow_path = os.path.join(os.path.dirname(images[0]), f'slideshow_{job_id}.html')
    with open(slideshow_path, 'w') as f:
        f.write(html_content)
    
    return slideshow_path

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
            'virtual_tour': f'virtual_tour_{job_id}.html',
            'description': f'property_description_{job_id}.txt',
            'script': f'voiceover_script_{job_id}.txt',
            'slideshow': f'slideshow_{job_id}.html'
        }
        
        if file_type not in file_mapping:
            return jsonify({'error': 'Invalid file type'}), 400
        
        filepath = os.path.join(job_dir, file_mapping[file_type])
        
        if not os.path.exists(filepath) and file_type == 'slideshow':
            # Generate slideshow on demand if not exists
            image_files = sorted([f for f in os.listdir(job_dir) if f.startswith('opt_') and f.endswith('.jpg')])
            if image_files:
                images = []
                for img_file in image_files:
                    with open(os.path.join(job_dir, img_file), 'rb') as f:
                        images.append(base64.b64encode(f.read()).decode('utf-8'))
                filepath = create_html_slideshow(images, job_id)
        
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