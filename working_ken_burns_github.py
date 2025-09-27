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
import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Using storage backend (Bunny.net)
from upload_to_storage import upload_files_to_storage, upload_video_to_storage, get_video_url_storage
from ai_script_generator import generate_room_scripts as ai_generate_room_scripts
from openai_tts import synthesize_speech, OpenAITTSError
from github_actions_integration import GitHubActionsIntegration
from PIL import Image
import io
from storage_adapter import test_storage_initialization

# Validate storage backend so uploads fail fast if credentials are missing
storage_ok, storage_backend = test_storage_initialization()
if not storage_ok:
    logger.warning('Storage backend initialization failed; uploads will return an error until storage is configured.')
else:
    logger.info('Storage backend ready: %s', storage_backend)

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


def _job_storage_dir(job_id: str) -> Path:
    base = Path(STORAGE_DIR)
    primary = base / job_id
    legacy = base / f'job_{job_id}'
    if primary.exists():
        return primary
    if legacy.exists():
        return legacy
    return primary


def _load_job_from_disk(job_id: str) -> Optional[Dict[str, Any]]:
    job_dir = _job_storage_dir(job_id)
    if not job_dir.exists():
        return None

    job_data: Dict[str, Any] = {
        'status': 'completed',
        'progress': 100,
        'current_step': 'Restored job from storage.',
        'video_available': False,
        'virtual_tour_available': False,
        'images_processed': 0,
        'files_generated': {},
        'room_assignments': [],
        'room_scripts': [],
        'talk_track': {
            'status': 'not_started',
            'progress': 0,
            'message': 'Narration ready for synthesis.'
        },
    }

    files_generated = job_data['files_generated']

    try:
        room_scripts_path = job_dir / f'room_scripts_{job_id}.json'
        if room_scripts_path.exists():
            job_data['room_scripts'] = json.loads(room_scripts_path.read_text(encoding='utf-8'))
            files_generated['room_scripts'] = job_data['room_scripts']
            files_generated['room_scripts_file'] = str(room_scripts_path)

        script_path = job_dir / f'voiceover_script_{job_id}.txt'
        if script_path.exists():
            files_generated['script'] = str(script_path)

        description_path = job_dir / f'property_description_{job_id}.txt'
        if description_path.exists():
            files_generated['description'] = str(description_path)

        local_video_path = job_dir / f'virtual_tour_{job_id}.mp4'
        if local_video_path.exists():
            files_generated['local_video'] = str(local_video_path)
            job_data['video_available'] = True

        narrated_video_path = job_dir / f'virtual_tour_{job_id}_narrated.mp4'
        if narrated_video_path.exists():
            files_generated['talk_track_video'] = str(narrated_video_path)

        talk_track_mp3 = job_dir / f'talk_track_{job_id}.mp3'
        if talk_track_mp3.exists():
            files_generated['talk_track_audio'] = str(talk_track_mp3)
            job_data['talk_track'] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Talk track audio ready.',
                'audio_file': talk_track_mp3.name,
            }
            if narrated_video_path.exists():
                job_data['talk_track']['video_file'] = narrated_video_path.name

        assignments_candidates = [
            job_dir / f'room_assignments_{job_id}.json',
            job_dir / 'room_assignments.json'
        ]
        for assignments_path in assignments_candidates:
            if assignments_path.exists():
                try:
                    job_data['room_assignments'] = json.loads(assignments_path.read_text(encoding='utf-8'))
                    files_generated['room_assignments'] = job_data['room_assignments']
                    files_generated['room_assignments_file'] = str(assignments_path)
                    break
                except json.JSONDecodeError:
                    logger.warning('Failed to parse room assignments for job %s', job_id)

        tour_path = Path(STORAGE_DIR) / f'{job_id}_tour.html'
        if tour_path.exists():
            job_data['virtual_tour_available'] = True
            files_generated['tour_html'] = str(tour_path)

        image_extensions = ('*.jpg', '*.jpeg', '*.png', '*.webp')
        image_files = []
        for pattern in image_extensions:
            image_files.extend(job_dir.glob(pattern))
        if image_files:
            job_data['images_processed'] = len(image_files)
            files_generated['image_count'] = len(image_files)

    except Exception as exc:
        logger.warning('Could not rebuild job %s from storage: %s', job_id, exc)

    active_jobs[job_id] = job_data
    return job_data


def _ensure_job(job_id: str) -> Optional[Dict[str, Any]]:
    job = active_jobs.get(job_id)
    if job:
        return job
    return _load_job_from_disk(job_id)


FFMPEG_BINARY = os.environ.get('FFMPEG_BINARY') or 'ffmpeg'
FFPROBE_BINARY = os.environ.get('FFPROBE_BINARY')
if not FFPROBE_BINARY:
    default_probe = 'ffprobe'
    if isinstance(FFMPEG_BINARY, str) and 'ffmpeg' in FFMPEG_BINARY.lower():
        default_probe = FFMPEG_BINARY.lower().replace('ffmpeg', 'ffprobe')
    FFPROBE_BINARY = default_probe
if isinstance(FFPROBE_BINARY, str) and not (Path(FFPROBE_BINARY).exists() or shutil.which(FFPROBE_BINARY)):
    try:
        import imageio_ffmpeg
        FFPROBE_BINARY = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
    except Exception:
        FFPROBE_BINARY = 'ffprobe'
SLIDE_DURATION_SECONDS = int(os.environ.get('SLIDE_DURATION_SECONDS', '8'))


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


def _build_job_payload(job_id: str) -> Optional[Dict[str, Any]]:
    job = _ensure_job(job_id)
    if not job:
        return None

    files_generated = job.get('files_generated', {})
    payload: Dict[str, Any] = {
        'job_id': job_id,
        'status': job.get('status', 'unknown'),
        'progress': job.get('progress', 0),
        'current_step': job.get('current_step', ''),
        'video_available': job.get('video_available', False),
        'virtual_tour_available': job.get('virtual_tour_available', False),
        'images_processed': job.get('images_processed', 0),
        'processing_time': job.get('processing_time', ''),
        'files_generated': files_generated,
        'room_assignments': job.get('room_assignments', []),
        'room_scripts': job.get('room_scripts', []),
        'talk_track': job.get('talk_track', {}),
        'github_job_id': job.get('github_job_id'),
        'github_actions_failed': job.get('github_actions_failed', False),
        'imagekit_video': job.get('imagekit_video', False),
        'bunnynet_video': job.get('bunnynet_video', False),
        'error': job.get('error'),
        'error_details': job.get('error_details'),
    }
    return payload

def _persist_room_scripts(job_id: str, scripts: List[str], job_dir: Path) -> None:
    job = active_jobs.get(job_id)
    if not job:
        return

    job_dir.mkdir(parents=True, exist_ok=True)

    job['room_scripts'] = scripts
    files_generated = job.setdefault('files_generated', {})
    files_generated['room_scripts'] = scripts

    scripts_path = job_dir / f'room_scripts_{job_id}.json'
    scripts_path.write_text(json.dumps(scripts, indent=2), encoding='utf-8')
    files_generated['room_scripts_file'] = str(scripts_path)

    script_path = job_dir / f'voiceover_script_{job_id}.txt'
    script_path.write_text(generate_voiceover_script(scripts), encoding='utf-8')
    files_generated['script'] = str(script_path)

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

def generate_property_description(num_images: int) -> str:
    return (
        "STUNNING LUXURY PROPERTY - VIRTUAL TOUR\n\n"
        f"Experience this exceptional property through our professional virtual tour featuring {num_images} carefully selected views.\n\n"
        "PROPERTY HIGHLIGHTS:\n"
        "- Meticulously maintained and presented\n"
        "- Thoughtfully designed living spaces\n"
        "- Premium finishes throughout\n"
        "- Abundant natural light\n"
        "- Professional photography showcasing every detail\n\n"
        "This virtual tour captures the essence and elegance of this remarkable property. Each image has been professionally captured to highlight the unique features and characteristics that make this home truly special.\n\n"
        "For more information or to schedule a private showing, please contact your real estate professional.\n\n"
        f"Virtual Tour Created: {datetime.now().strftime('%B %d, %Y')}\n"
    )

def generate_voiceover_script(room_scripts: List[str]) -> str:
    if not room_scripts:
        return (
            "VIRTUAL TOUR VOICEOVER SCRIPT\n\n"
            "No narration lines are available yet.\n"
            "Edit the narration for each slide and approve the talk track to generate audio.\n"
        )

    lines = [
        'VIRTUAL TOUR VOICEOVER SCRIPT',
        '',
        f'Each scene below is timed for approximately {SLIDE_DURATION_SECONDS} seconds.',
        'Adjust any line before approving the talk track.',
        '',
    ]

    for index, entry in enumerate(room_scripts, start=1):
        lines.append(f'Scene {index} ({SLIDE_DURATION_SECONDS} seconds):')
        lines.append(entry)
        lines.append('')

    lines.append('Once finalized, approve the script to synthesize the narrated audio track.')
    return '\n'.join(lines)

def _run_subprocess(cmd: List[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or 'Command failed')
    return result

def _probe_audio_duration(audio_path: Path) -> float:
    cmd = [FFPROBE_BINARY or 'ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)]
    try:
        result = _run_subprocess(cmd)
        return float(result.stdout.strip())
    except Exception:
        ffmpeg_cmd = [FFMPEG_BINARY, '-hide_banner', '-i', str(audio_path)]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
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
            escaped = str(segment).replace("'", "'\\''")
            handle.write(f"file '{escaped}'\n")

    cmd = [FFMPEG_BINARY, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file), '-c', 'pcm_s16le', '-ar', '48000', '-ac', '2', str(output_path)]
    _run_subprocess(cmd)

def _convert_audio_to_mp3(source: Path, output: Path) -> None:
    cmd = [FFMPEG_BINARY, '-y', '-i', str(source), '-c:a', 'libmp3lame', '-b:a', '192k', str(output)]
    _run_subprocess(cmd)

def _download_remote_video(job: Dict[str, Any], job_id: str, job_dir: Path) -> Optional[Path]:
    files_generated = job.get('files_generated', {})
    video_url = files_generated.get('bunnynet_url') or files_generated.get('imagekit_url') or files_generated.get('cloud_video_url')
    if not video_url:
        return None

    target_path = job_dir / f'remote_video_{job_id}.mp4'
    try:
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        with target_path.open('wb') as handle:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    handle.write(chunk)
        return target_path
    except Exception as exc:
        logger.warning(f'Unable to download remote video for merge: {exc}')
        return None

def _merge_audio_with_video(job_id: str, job_dir: Path, audio_path: Path) -> Optional[Path]:
    job = active_jobs.get(job_id, {})
    files_generated = job.get('files_generated', {})

    local_video = files_generated.get('local_video')
    if local_video and os.path.exists(local_video):
        video_source = Path(local_video)
    else:
        candidate = job_dir / f'virtual_tour_{job_id}.mp4'
        video_source = candidate if candidate.exists() else None

    if not video_source:
        if not job.get('video_available'):
            logger.info('Video not yet available for job %s; skipping merge step.', job_id)
            return None
        video_source = _download_remote_video(job, job_id, job_dir)
        if not video_source:
            logger.info('Remote video could not be obtained for job %s; skipping merge.', job_id)
            return None

    output_path = job_dir / f'virtual_tour_{job_id}_narrated.mp4'
    cmd = [
        FFMPEG_BINARY, '-y',
        '-i', str(video_source),
        '-i', str(audio_path),
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output_path)
    ]
    _run_subprocess(cmd)
    return output_path

def _generate_talk_track_async(job_id: str, scripts: List[str]) -> None:
    job = active_jobs.get(job_id)
    if not job:
        return

    job_dir = Path(STORAGE_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
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
            job['talk_track']['progress'] = 10 + int(idx / max(len(scripts), 1) * 35)

        job['talk_track'].update({'progress': 55, 'message': 'Combining narration segments'})
        talk_track_wav = job_dir / f'talk_track_{job_id}.wav'
        _concat_audio_segments(segments, talk_track_wav)
        talk_track_mp3 = job_dir / f'talk_track_{job_id}.mp3'
        _convert_audio_to_mp3(talk_track_wav, talk_track_mp3)

        files_generated = job.setdefault('files_generated', {})
        files_generated['talk_track_audio'] = str(talk_track_mp3)

        job['talk_track'].update({'progress': 75, 'message': 'Attempting to merge narration with video'})
        merged_video = None
        try:
            merged_video = _merge_audio_with_video(job_id, job_dir, talk_track_mp3)
        except Exception as merge_exc:
            logger.warning('Talk track merge failed for job %s: %s', job_id, merge_exc)

        if merged_video and merged_video.exists():
            files_generated['talk_track_video'] = str(merged_video)
            job['talk_track'] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Talk track ready and merged with video.',
                'audio_file': talk_track_mp3.name,
                'video_file': merged_video.name,
            }
        else:
            job['talk_track'] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Talk track audio ready. Video merge skipped.',
                'audio_file': talk_track_mp3.name,
            }

    except OpenAITTSError as exc:
        logger.error('OpenAI TTS failed for job %s: %s', job_id, exc)
        job['talk_track'] = {'status': 'failed', 'progress': 0, 'message': f'TTS failed: {exc}'}
    except Exception as exc:
        logger.exception('Talk track generation failed for job %s', job_id)
        job['talk_track'] = {'status': 'failed', 'progress': 0, 'message': str(exc)}

def format_room_label(room_value: str, other_label: str = "") -> str:
    if not room_value:
        return 'Unassigned'
    if room_value == 'other':
        return other_label.strip() or 'Other'
    return ROOM_LABELS.get(room_value, room_value)


def start_github_actions_polling(job_id, github_job_id):
    """Start a background thread to poll GitHub Actions and then ImageKit for the completed video"""
    def poll_for_video():
        logger.info(f"Starting GitHub Actions polling for job {job_id}, GitHub job ID: {github_job_id}")
        
        max_attempts = 45  # Poll for up to 7.5 minutes (45 * 10 seconds) - reduced for faster failure reporting
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
                            active_jobs[job_id]['github_actions_failed'] = True
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
        
        # Timeout - video generation took too long
        logger.error(f"Video polling timeout for job {job_id} after {max_attempts} attempts")
        active_jobs[job_id]['status'] = 'error'
        active_jobs[job_id]['current_step'] = 'Remotion timeout - no video generated'
        active_jobs[job_id]['progress'] = 100
        active_jobs[job_id]['github_actions_failed'] = True
        return

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
            'files_generated': {},
            'room_assignments': [],
            'room_scripts': [],
            'talk_track': {'status': 'not_started', 'progress': 0, 'message': 'Narration not generated yet.'}
        }
        global storage_ok, storage_backend
        if not storage_ok:
            storage_ok, storage_backend = test_storage_initialization()
        if not storage_ok:
            error_message = (
                'Storage backend not configured. Configure Bunny.net credentials '
                '(BUNNY_STORAGE_ZONE_NAME, BUNNY_ACCESS_KEY, BUNNY_PULL_ZONE_URL).'
            )
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = error_message
            active_jobs[job_id]['error'] = error_message
            return jsonify({'error': error_message, 'job_id': job_id}), 503

        if os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() != 'true':
            error_message = 'GitHub Actions workflow disabled. Set USE_GITHUB_ACTIONS=true to enable rendering.'
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = error_message
            active_jobs[job_id]['error'] = error_message
            return jsonify({'error': error_message, 'job_id': job_id}), 503

        if github_actions is None or not getattr(github_actions, 'is_valid', True):
            error_message = 'GitHub Actions credentials missing or invalid. Check GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO.'
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = error_message
            active_jobs[job_id]['error'] = error_message
            return jsonify({'error': error_message, 'job_id': job_id}), 503

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

        normalized_property_details = {
            'address': full_address,
            'details1': details1,
            'details2': details2,
            'agent_name': agent_name,
            'agent_email': agent_email,
            'agent_phone': agent_phone,
            'brand_name': brand_name
        }
        
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
            room_assignment_payload = []
            raw_assignments = request.form.get('room_assignments')
            if raw_assignments:
                try:
                    parsed_assignments = json.loads(raw_assignments)
                    if isinstance(parsed_assignments, list):
                        room_assignment_payload = parsed_assignments
                except json.JSONDecodeError:
                    logger.warning('Invalid room_assignments payload; ignoring')

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

                            assignment_info = room_assignment_payload[actual_index] if actual_index < len(room_assignment_payload) else {}
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
            active_jobs[job_id]['files_generated']['image_count'] = len(saved_files)
            active_jobs[job_id]['files_generated']['room_assignments'] = active_jobs[job_id]['room_assignments']
            assignments_path = Path(job_dir) / f'room_assignments_{job_id}.json'
            assignments_path.write_text(json.dumps(active_jobs[job_id]['room_assignments'], indent=2), encoding='utf-8')
            active_jobs[job_id]['files_generated']['room_assignments_file'] = str(assignments_path)
            room_scripts = ai_generate_room_scripts(
                active_jobs[job_id]['room_assignments'],
                normalized_property_details,
                Path(job_dir)
            ) or []
            _persist_room_scripts(job_id, room_scripts, Path(job_dir))

            description_text = generate_property_description(len(active_jobs[job_id]['room_assignments']))
            description_path = Path(job_dir) / f'property_description_{job_id}.txt'
            description_path.write_text(description_text, encoding='utf-8')
            active_jobs[job_id]['files_generated']['description'] = str(description_path)
            if original_total_size > 0:
                total_compression = (1 - compressed_total_size / original_total_size) * 100
                active_jobs[job_id]['current_step'] = f'Compressed {len(saved_files)} images (saved {total_compression:.0f}% space)'
                logger.info(f"Total compression: {original_total_size/1024/1024:.1f}MB -> {compressed_total_size/1024/1024:.1f}MB")
            else:
                active_jobs[job_id]['current_step'] = f'Saved {len(saved_files)} images'
            active_jobs[job_id]['progress'] = 10
            
            # Only use GitHub Actions + Remotion for video generation
            # No local fallback - GitHub Actions must be properly configured
        
        # Check if we should use GitHub Actions for high-quality rendering
        use_github_actions = os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() == 'true' and github_actions
        logger.info(f"GitHub Actions enabled: {use_github_actions} (env: {os.environ.get('USE_GITHUB_ACTIONS')}, integration: {github_actions is not None})")
        
        # Prepare image URLs for GitHub Actions
        github_image_urls = image_urls or []
        
        # If we have uploaded files but no URLs, upload them to Cloudinary first
        if use_github_actions and 'saved_files' in locals() and saved_files and not image_urls:
            try:
                active_jobs[job_id]['current_step'] = 'Uploading images to storage for GitHub Actions'
                active_jobs[job_id]['progress'] = 40
                
                # Upload files to storage backend
                logger.info(f"Uploading {len(saved_files)} files to storage backend...")
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
                
                logger.info(f"Upload result: got {len(github_image_urls) if github_image_urls else 0} URLs back")
                if not github_image_urls:
                    logger.error("No URLs returned from upload_files_to_storage - upload completely failed")
                
                if github_image_urls:
                    logger.info(f"Successfully uploaded {len(github_image_urls)} images")
                    for i, url in enumerate(github_image_urls):
                        logger.info(f"  Uploaded URL {i+1}: {url}")
                    active_jobs[job_id]['current_step'] = f'Uploaded {len(github_image_urls)} images to cloud'
                    active_jobs[job_id]['progress'] = 50
                else:
                    error_msg = f"Failed to upload images to {backend_name} - check storage credentials"
                    logger.error(error_msg)
                    active_jobs[job_id]['current_step'] = error_msg
                    github_image_urls = []
                    
            except Exception as e:
                error_msg = f"Error uploading to storage: {str(e)}"
                logger.error(error_msg)
                active_jobs[job_id]['current_step'] = error_msg
                github_image_urls = []
        
        # Track whether we attempted GitHub Actions
        github_actions_attempted = False
        
        # Log why GitHub Actions might not be used
        if not use_github_actions:
            logger.info("GitHub Actions not enabled (USE_GITHUB_ACTIONS != 'true' or watermark requested)")
        elif not github_image_urls:
            logger.error("GitHub Actions enabled but no images uploaded to storage; aborting job")
        
        if use_github_actions and not github_image_urls:
            error_msg = 'Failed to upload images to storage for GitHub Actions. Verify Bunny.net credentials.'
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['current_step'] = error_msg
            active_jobs[job_id]['error'] = error_msg
            active_jobs[job_id]['progress'] = 100
            active_jobs[job_id]['github_actions_failed'] = True
            return jsonify({'error': error_msg, 'job_id': job_id}), 502

        if use_github_actions and github_image_urls:
            github_actions_attempted = True
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
                
                # Prepare watermark configuration if available
                watermark_config = None  # Watermark embedding disabled

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
                        },
                        watermark=watermark_config
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
                    
                    # Mark that GitHub Actions failed
                    active_jobs[job_id]['github_actions_failed'] = True
                    logger.error("GitHub Actions failed - no video will be generated")
                    
            except Exception as e:
                logger.error(f"Error with GitHub Actions: {e}")
                active_jobs[job_id]['current_step'] = f'GitHub Actions error: {str(e)}'
                # Mark that GitHub Actions failed
                active_jobs[job_id]['github_actions_failed'] = True
                logger.error("GitHub Actions error occurred - no video will be generated")
        
        
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
        
        # If GitHub Actions was triggered successfully, start polling for the video
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
            # GitHub Actions was not triggered successfully
            logger.error(f"GitHub Actions not triggered for job {job_id}")
            active_jobs[job_id]['status'] = 'error'
            active_jobs[job_id]['progress'] = 100
            
            if active_jobs[job_id].get('github_actions_failed'):
                active_jobs[job_id]['current_step'] = 'GitHub Actions failed - check configuration'
            elif not use_github_actions:
                active_jobs[job_id]['current_step'] = 'GitHub Actions not enabled'
            elif not github_image_urls:
                active_jobs[job_id]['current_step'] = 'Failed to upload images to storage'
            else:
                active_jobs[job_id]['current_step'] = 'Failed to trigger GitHub Actions'
            
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
        job = _ensure_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        
        # Check if video is on Bunny.net (GitHub Actions workflow)
        if job.get('bunnynet_video') and job.get('files_generated', {}).get('bunnynet_url'):
            bunnynet_url = job['files_generated']['bunnynet_url']
            # Redirect to Bunny.net URL for download
            return redirect(bunnynet_url)
        
        # Fallback: If we have a GitHub job ID but webhook hasn't updated yet
        if job.get('github_job_id'):
            github_job_id = job['github_job_id']
            # Use storage adapter for video URL (Bunny.net)
            try:
                from storage_adapter import get_storage
                storage = get_storage()
                video_url = storage.get_video_url(f"{github_job_id}.mp4", "tours/videos/")
                logger.info(f"Got video URL from storage adapter: {video_url}")
            except Exception as e:
                logger.error(f"Failed to get video URL from storage: {e}")
                # Fallback to Bunny.net direct URL if storage adapter fails
                bunny_url = os.environ.get('BUNNY_PULL_ZONE_URL', '')
                if not bunny_url:
                    logger.error("BUNNY_PULL_ZONE_URL not configured")
                    return jsonify({'error': 'Video storage not configured'}), 500
                if not bunny_url.endswith('/'):
                    bunny_url += '/'
                video_url = f"{bunny_url}tours/videos/{github_job_id}.mp4"
            
            # Check if video exists on Bunny.net
            try:
                import requests
                response = requests.head(video_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Video found on Bunny.net for job {job_id}")
                    # Update job status  
                    job['bunnynet_video'] = True
                    job['video_available'] = True
                    if 'files_generated' not in job:
                        job['files_generated'] = {}
                    job['files_generated']['bunnynet_url'] = video_url
                    # Redirect to the video
                    return redirect(video_url)
                else:
                    logger.info(f"Bunny.net URL not found (status {response.status_code}), will serve from local storage")
            except Exception as e:
                logger.info(f"Bunny.net check failed ({e}), will serve from local storage")
        
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
        job = _ensure_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
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
        job = _ensure_job(job_id)
        # First check if this is a GitHub Actions job
        if job:
            job = active_jobs[job_id]
            
            # For video files from GitHub Actions
            if file_type in ['video', 'virtual_tour']:
                # First priority: Check for stored Bunny.net URL
                if job.get('files_generated', {}).get('bunnynet_url'):
                    bunnynet_url = job['files_generated']['bunnynet_url']
                    logger.info(f"Using stored Bunny.net URL for job {job_id}: {bunnynet_url}")
                    return redirect(bunnynet_url)
                
                # Second priority: If we have a GitHub job ID, check if Bunny.net URL exists
                elif job.get('github_job_id'):
                    github_job_id = job['github_job_id']
                    # Use storage adapter for video URL
                    try:
                        from storage_adapter import get_storage
                        storage = get_storage()
                        video_url = storage.get_video_url(f"{github_job_id}.mp4", "tours/videos/")
                    except Exception as e:
                        logger.error(f"Failed to get video URL from storage: {e}")
                        # Fallback to Bunny.net direct URL
                        bunny_url = os.environ.get('BUNNY_PULL_ZONE_URL', '')
                        if not bunny_url:
                            logger.error("BUNNY_PULL_ZONE_URL not configured")
                            return jsonify({'error': 'Video storage not configured'}), 500
                        if not bunny_url.endswith('/'):
                            bunny_url += '/'
                        video_url = f"{bunny_url}tours/videos/{github_job_id}.mp4"
                    
                    # Check if the Bunny.net URL actually exists before redirecting
                    try:
                        import requests
                        response = requests.head(video_url, timeout=5)
                        if response.status_code == 200:
                            logger.info(f"Bunny.net URL exists, redirecting for job {job_id}: {video_url}")
                            
                            # Update job data for future requests
                            job['bunnynet_video'] = True
                            job['video_available'] = True
                            if 'files_generated' not in job:
                                job['files_generated'] = {}
                            job['files_generated']['bunnynet_url'] = video_url
                            
                            return redirect(video_url)
                        else:
                            logger.info(f"Bunny.net URL not found (status {response.status_code}), will serve from local storage")
                    except Exception as e:
                        logger.info(f"Bunny.net check failed ({e}), will serve from local storage")
                    
                    # If we get here, Bunny.net doesn't have the video, so continue to serve from local
                
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
        
        # Fallback to job directory lookup using persisted storage
        job_dir_path = _job_storage_dir(job_id)
        if not job_dir_path.exists():
            return jsonify({'error': 'Job not found'}), 404
        job_dir = str(job_dir_path)

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

@virtual_tour_bp.route('/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    payload = _build_job_payload(job_id)
    if not payload:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(payload)

@virtual_tour_bp.route('/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    """Get status of a specific job"""
    job = _ensure_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    job = active_jobs[job_id]
    
    # REMOVED GitHub API status checking to prevent rate limit exhaustion
    # The Cloudinary polling thread already handles checking for video completion
    # Each status check was making an API call, causing 30+ calls per minute
    
    # Fallback: Check if video exists on storage directly
    if job.get('github_job_id') and job.get('status') != 'completed':
        try:
            from storage_adapter import get_storage
            storage = get_storage()
            video_url = storage.get_video_url(f"{job['github_job_id']}.mp4", "tours/videos/")
        except Exception as e:
            logger.error(f"Failed to get video URL from storage: {e}")
            # Fallback to ImageKit
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
    
    payload = _build_job_payload(job_id)
    if not payload:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(payload)

@virtual_tour_bp.route('/job/<job_id>/scripts', methods=['PUT'])
def update_job_scripts(job_id):
    job = _ensure_job(job_id)
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

    job_dir = Path(STORAGE_DIR) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
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
    job = _ensure_job(job_id)
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

    job_dir = Path(STORAGE_DIR) / job_id
    _persist_room_scripts(job_id, sanitized, job_dir)

    job['talk_track'] = {'status': 'in_progress', 'progress': 5, 'message': 'Submitting narration for synthesis'}
    threading.Thread(target=_generate_talk_track_async, args=(job_id, sanitized), daemon=True).start()

    return jsonify({'status': 'queued', 'job_id': job_id})




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
