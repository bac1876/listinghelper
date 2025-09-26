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
import re
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ffmpeg_ken_burns import create_ken_burns_video, get_ffmpeg_binary
from cloudinary_integration import generate_cloudinary_video
try:
    from creatomate_integration_v2 import create_real_estate_video
    CREATOMATE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Creatomate integration not available: {e}")
    CREATOMATE_AVAILABLE = False

from openai_tts import synthesize_speech, OpenAITTSError
from ai_script_generator import generate_room_scripts as ai_generate_room_scripts

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# Railway storage directory
STORAGE_DIR = '/app/storage'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory job tracking with detailed status
active_jobs = {}

FFMPEG_BINARY = get_ffmpeg_binary() or 'ffmpeg'
FFPROBE_BINARY = os.getenv('FFPROBE_BINARY')
if not FFPROBE_BINARY:
    if isinstance(FFMPEG_BINARY, str) and 'ffmpeg' in FFMPEG_BINARY.lower():
        FFPROBE_BINARY = FFMPEG_BINARY.lower().replace('ffmpeg', 'ffprobe')
    else:
        FFPROBE_BINARY = 'ffprobe'

if isinstance(FFPROBE_BINARY, str):
    probe_path = Path(FFPROBE_BINARY)
    if not probe_path.exists() and shutil.which(FFPROBE_BINARY) is None:
        try:
            import imageio_ffmpeg
            FFPROBE_BINARY = imageio_ffmpeg.get_ffprobe_exe()
        except Exception:
            FFPROBE_BINARY = 'ffprobe'
SLIDE_DURATION_SECONDS = int(os.getenv('SLIDE_DURATION_SECONDS', '8'))

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


def _build_job_payload(job_id):
    job = active_jobs.get(job_id)
    if not job:
        return None
    return {
        'job_id': job_id,
        'status': job.get('status', 'unknown'),
        'progress': job.get('progress', 0),
        'current_step': job.get('current_step', ''),
        'video_available': job.get('video_available', False),
        'virtual_tour_available': job.get('video_available', False),
        'cloudinary_video': job.get('cloudinary_video', False),
        'images_processed': job.get('images_processed', 0),
        'processing_time': job.get('processing_time', ''),
        'files_generated': job.get('files_generated', {}),
        'room_assignments': job.get('room_assignments', []),
        'room_scripts': job.get('room_scripts', []),
        'talk_track': job.get('talk_track', {}),
        'error': job.get('error'),
        'error_details': job.get('error_details'),
    }


def _persist_room_scripts(job_id: str, scripts: List[str], job_dir: Path) -> None:
    job = active_jobs.get(job_id)
    if not job:
        return
    job['room_scripts'] = scripts
    job['files_generated']['room_scripts'] = scripts
    scripts_path = job_dir / f'room_scripts_{job_id}.json'
    scripts_path.write_text(json.dumps(scripts, indent=2))
    job['files_generated']['room_scripts_file'] = scripts_path.name
    script_path = job_dir / f'voiceover_script_{job_id}.txt'
    script_path.write_text(generate_voiceover_script(scripts))
    job['files_generated']['script'] = script_path.name



def _sanitize_script_lines(scripts: List[str], expected_count: Optional[int] = None) -> List[str]:
    cleaned: List[str] = []
    for idx, entry in enumerate(scripts, start=1):
        text_line = str(entry).strip()
        if not text_line:
            raise ValueError(f'Scene {idx} has no narration. Please add text.')
        cleaned.append(text_line)

    if expected_count is not None and len(cleaned) != expected_count:
        raise ValueError(f'Expected {expected_count} narration lines, received {len(cleaned)}.')

    return cleaned


def format_room_label(room_value: str, other_label: str = "") -> str:
    if not room_value:
        return 'Unassigned'
    if room_value == 'other':
        return other_label.strip() or 'Other'
    return ROOM_LABELS.get(room_value, room_value)


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
        if request.is_json:
            payload = request.get_json(silent=True)
            if payload and 'job_id' in payload:
                check_job_id = payload['job_id']
                if check_job_id in active_jobs:
                    job_payload = _build_job_payload(check_job_id)
                    if job_payload:
                        return jsonify(job_payload)
        
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
            'room_assignments': [],
            'room_scripts': [],
            'talk_track': {'status': 'not_started', 'progress': 0}
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
        active_jobs[job_id]['property_details'] = property_details
        
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

        active_jobs[job_id]['images_processed'] = len(saved_paths)
        active_jobs[job_id]['files_generated']['image_count'] = len(saved_paths)
        active_jobs[job_id]['files_generated']['room_assignments'] = active_jobs[job_id]['room_assignments']
        room_scripts = ai_generate_room_scripts(
            active_jobs[job_id]['room_assignments'],
            property_details,
            job_dir
        )
        _persist_room_scripts(job_id, room_scripts, job_dir)
        
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
            
            script_text = generate_voiceover_script(room_scripts)
            script_path = os.path.join(job_dir, f'voiceover_script_{job_id}.txt')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_text)
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
        
        return jsonify(_build_job_payload(job_id))
        
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

def generate_voiceover_script(room_scripts: List[str]) -> str:
    """Create a formatted narration outline using the current room scripts."""
    if not room_scripts:
        return """VIRTUAL TOUR VOICEOVER SCRIPT

No narration lines are available yet.
Edit the narration for each slide and approve the talk track to generate audio.
"""

    lines = [
        "VIRTUAL TOUR VOICEOVER SCRIPT",
        "",
        f"Each scene below is timed for approximately {SLIDE_DURATION_SECONDS} seconds.",
        "Adjust any line before approving the talk track.",
        "",
    ]

    for index, entry in enumerate(room_scripts, start=1):
        lines.append(f"Scene {index} ({SLIDE_DURATION_SECONDS} seconds):")
        lines.append(entry)
        lines.append("")

    lines.append("Once finalized, approve the script to synthesize the narrated audio track.")
    return '\n'.join(lines)



def _run_subprocess(cmd: List[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'Command failed')
    return result

def _probe_audio_duration(audio_path: Path) -> float:
    cmd = [FFPROBE_BINARY, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
    try:
        result = _run_subprocess(cmd)
        return float(result.stdout.strip())
    except Exception:
        ffmpeg_cmd = [FFMPEG_BINARY, '-hide_banner', '-i', str(audio_path)]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
        output = result.stderr or result.stdout or ''
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", output)
        if not match:
            raise RuntimeError(f'Unable to determine duration for {audio_path}')
        hours, minutes, seconds = match.groups()
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + float(seconds)
        return float(total_seconds)

def _prepare_talk_segment(segment_path: Path, idx: int) -> Path:
    target = SLIDE_DURATION_SECONDS
    duration = _probe_audio_duration(segment_path)
    if duration > target + 0.5:
        raise ValueError(f'Scene {idx} narration is too long ({duration:.1f}s). Shorten it to fit {target} seconds.')

    padded_path = segment_path.with_suffix('.wav')
    cmd = [FFMPEG_BINARY, '-y', '-i', str(segment_path), '-ar', '48000', '-ac', '2']
    if duration < target:
        pad_seconds = target - duration
        cmd += ['-af', f'apad=pad_dur={pad_seconds:.2f}', '-t', f'{target:.2f}']
    else:
        cmd += ['-t', f'{target:.2f}']
    cmd.append(str(padded_path))
    _run_subprocess(cmd)
    return padded_path

def _concat_audio_segments(segments: List[Path], output_path: Path) -> None:
    concat_file = output_path.with_suffix('.txt')
    with concat_file.open('w', encoding='utf-8') as handle:
        for segment in segments:
            escaped = str(segment).replace("'", "'\''")
            handle.write(f"file '{escaped}'\n")

    cmd = [FFMPEG_BINARY, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'pcm_s16le', '-ar', '48000', '-ac', '2', str(output_path)]
    _run_subprocess(cmd)

def _convert_audio_to_mp3(source: Path, output: Path) -> None:
    cmd = [FFMPEG_BINARY, '-y', '-i', str(source), '-c:a', 'libmp3lame', '-b:a', '192k', str(output)]
    _run_subprocess(cmd)

def _merge_audio_with_video(job_id: str, job_dir: Path, audio_path: Path) -> Path:
    video_path = job_dir / f'virtual_tour_{job_id}.mp4'
    silent_path = job_dir / f'virtual_tour_{job_id}_silent.mp4'

    if not silent_path.exists():
        if not video_path.exists():
            raise FileNotFoundError('Base video not found for talk track merge')
        os.replace(video_path, silent_path)

    temp_output = job_dir / f'virtual_tour_{job_id}_with_audio.mp4'
    cmd = [
        FFMPEG_BINARY, '-y',
        '-i', str(silent_path),
        '-i', str(audio_path),
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(temp_output)
    ]
    _run_subprocess(cmd)
    final_path = job_dir / f'virtual_tour_{job_id}.mp4'
    os.replace(temp_output, final_path)
    return final_path

def _generate_talk_track_async(job_id: str, scripts: List[str]) -> None:
    job = active_jobs.get(job_id)
    if not job:
        return

    job_dir = Path(STORAGE_DIR) / f'job_{job_id}'
    job.setdefault('talk_track', {})
    job['talk_track'].update({'status': 'in_progress', 'progress': 10, 'message': 'Generating narration segments'})

    segments: List[Path] = []
    try:
        for idx, line in enumerate(scripts, start=1):
            audio_bytes = synthesize_speech(line)
            segment_path = job_dir / f'talk_segment_{idx:03d}.mp3'
            segment_path.write_bytes(audio_bytes)
            padded = _prepare_talk_segment(segment_path, idx)
            segments.append(padded)
            job['talk_track']['progress'] = 10 + int(idx / max(len(scripts), 1) * 40)

        job['talk_track'].update({'progress': 60, 'message': 'Combining narration'})
        talk_track_wav = job_dir / f'talk_track_{job_id}.wav'
        _concat_audio_segments(segments, talk_track_wav)
        talk_track_mp3 = job_dir / f'talk_track_{job_id}.mp3'
        _convert_audio_to_mp3(talk_track_wav, talk_track_mp3)

        job['talk_track'].update({'progress': 80, 'message': 'Merging audio with video'})
        final_video = _merge_audio_with_video(job_id, job_dir, talk_track_mp3)

        job['files_generated']['talk_track_audio'] = talk_track_mp3.name
        job['files_generated']['silent_video'] = f'virtual_tour_{job_id}_silent.mp4'
        job['files_generated']['video'] = final_video.name
        job['talk_track'] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Talk track ready',
            'audio_file': talk_track_mp3.name,
            'video_file': final_video.name,
        }
        job['video_available'] = True
        job['virtual_tour_available'] = True
    except OpenAITTSError as exc:
        logger.error('OpenAI TTS failed for job %s: %s', job_id, exc)
        job['talk_track'] = {'status': 'failed', 'progress': 0, 'message': f'TTS failed: {exc}'}
    except Exception as exc:
        logger.exception('Talk track generation failed for job %s', job_id)
        job['talk_track'] = {'status': 'failed', 'progress': 0, 'message': str(exc)}


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
            'script': f'voiceover_script_{job_id}.txt',
            'room_scripts': f'room_scripts_{job_id}.json',
            'talk_track': f'talk_track_{job_id}.mp3',
            'silent_video': f'virtual_tour_{job_id}_silent.mp4'
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
            'images_processed': job_data.get('images_processed', 0),
            'talk_track_status': job_data.get('talk_track', {}).get('status')
        })
    
    return jsonify({
        'jobs': jobs_list,
        'total': len(jobs_list)
    })

@virtual_tour_bp.route('/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    payload = _build_job_payload(job_id)
    if not payload:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(payload)

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
    
    payload = _build_job_payload(job_id)
    if not payload:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(payload)

@virtual_tour_bp.route('/job/<job_id>/scripts', methods=['PUT'])
def update_job_scripts(job_id):
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json(silent=True) or {}
    scripts = data.get('scripts')
    if not isinstance(scripts, list):
        return jsonify({'error': 'Invalid scripts payload'}), 400

    expected = len(job.get('room_assignments', [])) or None
    try:
        sanitized = _sanitize_script_lines(scripts, expected)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    job_dir = Path(STORAGE_DIR) / f'job_{job_id}'
    _persist_room_scripts(job_id, sanitized, job_dir)
    job['talk_track'] = {'status': 'not_started', 'progress': 0, 'message': 'Narration updated. Generate talk track to apply changes.'}

    payload = _build_job_payload(job_id)
    return jsonify({
        'job_id': job_id,
        'room_scripts': sanitized,
        'talk_track': job.get('talk_track'),
        'files_generated': payload['files_generated'] if payload else job.get('files_generated', {})
    })


@virtual_tour_bp.route('/job/<job_id>/talk-track', methods=['POST'])
def generate_talk_track(job_id):
    job = active_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json(silent=True) or {}
    scripts = data.get('scripts')
    if scripts is None:
        scripts = job.get('room_scripts')

    if not scripts:
        return jsonify({'error': 'No narration lines available for this job.'}), 400

    expected = len(job.get('room_assignments', [])) or None
    try:
        sanitized = _sanitize_script_lines(scripts, expected)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    talk_track = job.get('talk_track') or {}
    if talk_track.get('status') == 'in_progress':
        return jsonify({'error': 'Talk track generation already in progress'}), 409

    job_dir = Path(STORAGE_DIR) / f'job_{job_id}'
    _persist_room_scripts(job_id, sanitized, job_dir)

    job['talk_track'] = {'status': 'in_progress', 'progress': 5, 'message': 'Submitting narration for synthesis'}

    thread = threading.Thread(target=_generate_talk_track_async, args=(job_id, sanitized), daemon=True)
    thread.start()

    return jsonify({'status': 'queued', 'job_id': job_id})
