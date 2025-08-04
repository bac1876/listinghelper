"""
Enhanced download endpoint with better error handling and logging
This code should replace the download_file function in working_ken_burns.py
"""

import os
import time
import logging
from flask import jsonify, send_file
from datetime import datetime

logger = logging.getLogger(__name__)

@virtual_tour_bp.route('/download/<job_id>/<file_type>', methods=['GET'])
def download_file(job_id, file_type):
    """Enhanced download endpoint with detailed logging and error handling"""
    start_time = time.time()
    request_id = f"{job_id}_{file_type}_{int(start_time)}"
    
    logger.info(f"[{request_id}] Download request received - Job: {job_id}, Type: {file_type}")
    
    try:
        # Validate job_id format
        if not job_id or len(job_id) != 36:  # UUID length
            logger.error(f"[{request_id}] Invalid job_id format: {job_id}")
            return jsonify({
                'error': 'Invalid job ID format',
                'job_id': job_id,
                'request_id': request_id
            }), 400
        
        # Check job directory
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        logger.info(f"[{request_id}] Checking job directory: {job_dir}")
        
        if not os.path.exists(job_dir):
            logger.error(f"[{request_id}] Job directory not found: {job_dir}")
            
            # Check if job exists in memory
            if job_id in active_jobs:
                job_status = active_jobs[job_id].get('status', 'unknown')
                logger.info(f"[{request_id}] Job found in memory with status: {job_status}")
                
                if job_status == 'processing':
                    return jsonify({
                        'error': 'Job still processing',
                        'status': job_status,
                        'progress': active_jobs[job_id].get('progress', 0),
                        'request_id': request_id
                    }), 202  # Accepted but not ready
                    
            return jsonify({
                'error': 'Job not found',
                'job_id': job_id,
                'request_id': request_id,
                'suggestion': 'Job may have expired or been cleaned up'
            }), 404
        
        # Log directory contents for debugging
        try:
            dir_contents = os.listdir(job_dir)
            logger.info(f"[{request_id}] Job directory contents: {dir_contents}")
        except Exception as e:
            logger.error(f"[{request_id}] Error listing directory contents: {e}")
        
        # Map file types to actual filenames
        file_mapping = {
            'video': f'virtual_tour_{job_id}.mp4',
            'virtual_tour': f'virtual_tour_{job_id}.mp4',  # Backward compatibility
            'description': f'property_description_{job_id}.txt',
            'script': f'voiceover_script_{job_id}.txt'
        }
        
        if file_type not in file_mapping:
            logger.error(f"[{request_id}] Invalid file type requested: {file_type}")
            return jsonify({
                'error': 'Invalid file type',
                'requested': file_type,
                'valid_types': list(file_mapping.keys()),
                'request_id': request_id
            }), 400
        
        filename = file_mapping[file_type]
        filepath = os.path.join(job_dir, filename)
        logger.info(f"[{request_id}] Looking for file: {filepath}")
        
        # Check if file exists with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            if os.path.exists(filepath):
                # Check file size
                file_size = os.path.getsize(filepath)
                logger.info(f"[{request_id}] File found: {filename}, Size: {file_size} bytes")
                
                if file_size == 0:
                    logger.error(f"[{request_id}] File exists but is empty: {filepath}")
                    
                    # Check if still being written
                    if job_id in active_jobs and active_jobs[job_id].get('status') == 'processing':
                        return jsonify({
                            'error': 'File still being generated',
                            'status': 'processing',
                            'request_id': request_id
                        }), 202
                    
                    return jsonify({
                        'error': 'File is empty',
                        'file': filename,
                        'request_id': request_id
                    }), 500
                
                # File exists and has content - send it
                try:
                    logger.info(f"[{request_id}] Sending file: {filename}")
                    
                    # Add headers for better download handling
                    response = send_file(
                        filepath,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='video/mp4' if file_type in ['video', 'virtual_tour'] else 'text/plain'
                    )
                    
                    # Add custom headers
                    response.headers['X-Job-ID'] = job_id
                    response.headers['X-File-Size'] = str(file_size)
                    response.headers['X-Request-ID'] = request_id
                    
                    # Log successful download
                    elapsed_time = time.time() - start_time
                    logger.info(f"[{request_id}] Download successful - Time: {elapsed_time:.2f}s, Size: {file_size} bytes")
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"[{request_id}] Error sending file: {e}")
                    return jsonify({
                        'error': 'Error sending file',
                        'details': str(e),
                        'request_id': request_id
                    }), 500
            
            else:
                # File not found
                logger.warning(f"[{request_id}] File not found (attempt {attempt + 1}/{max_retries}): {filepath}")
                
                if attempt < max_retries - 1:
                    # Check if job is still processing
                    if job_id in active_jobs and active_jobs[job_id].get('status') == 'processing':
                        logger.info(f"[{request_id}] Job still processing, waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        continue
                    
                    # Check for alternative filenames
                    alt_files = [f for f in os.listdir(job_dir) if file_type in f or job_id in f]
                    if alt_files:
                        logger.info(f"[{request_id}] Found alternative files: {alt_files}")
                
        # File not found after all retries
        logger.error(f"[{request_id}] File not found after {max_retries} attempts: {filepath}")
        
        # Provide detailed error response
        error_response = {
            'error': 'File not found',
            'job_id': job_id,
            'file_type': file_type,
            'expected_file': filename,
            'request_id': request_id,
            'job_directory_exists': True,
            'directory_contents': dir_contents if 'dir_contents' in locals() else []
        }
        
        # Check if this is a Cloudinary video
        if file_type in ['video', 'virtual_tour'] and job_id in active_jobs:
            job_data = active_jobs[job_id]
            if job_data.get('cloudinary_video'):
                error_response['cloudinary_available'] = True
                error_response['cloudinary_url'] = job_data.get('files_generated', {}).get('cloud_video_url', '')
                error_response['suggestion'] = 'Video may be available on Cloudinary'
        
        return jsonify(error_response), 404
        
    except Exception as e:
        # Catch-all error handler
        elapsed_time = time.time() - start_time
        logger.error(f"[{request_id}] Unexpected error in download endpoint: {e}", exc_info=True)
        
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'request_id': request_id,
            'elapsed_time': f"{elapsed_time:.2f}s"
        }), 500


# Additional helper function for download diagnostics
@virtual_tour_bp.route('/download/<job_id>/diagnostics', methods=['GET'])
def download_diagnostics(job_id):
    """Diagnostic endpoint to help troubleshoot download issues"""
    try:
        diagnostics = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'storage_dir': STORAGE_DIR,
            'storage_exists': os.path.exists(STORAGE_DIR),
            'job_in_memory': job_id in active_jobs
        }
        
        # Check job directory
        job_dir = os.path.join(STORAGE_DIR, f'job_{job_id}')
        diagnostics['job_dir'] = job_dir
        diagnostics['job_dir_exists'] = os.path.exists(job_dir)
        
        if os.path.exists(job_dir):
            # List all files with details
            files = []
            for filename in os.listdir(job_dir):
                filepath = os.path.join(job_dir, filename)
                if os.path.isfile(filepath):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
                        'readable': os.access(filepath, os.R_OK)
                    })
            diagnostics['files'] = files
            diagnostics['file_count'] = len(files)
        
        # Check job status in memory
        if job_id in active_jobs:
            job_data = active_jobs[job_id]
            diagnostics['job_status'] = {
                'status': job_data.get('status'),
                'progress': job_data.get('progress'),
                'video_available': job_data.get('video_available'),
                'cloudinary_video': job_data.get('cloudinary_video'),
                'files_generated': job_data.get('files_generated', {}),
                'error': job_data.get('error')
            }
        
        # Check storage space
        try:
            stat = os.statvfs(STORAGE_DIR)
            diagnostics['storage_space'] = {
                'free_mb': (stat.f_bavail * stat.f_frsize) / (1024 * 1024),
                'total_mb': (stat.f_blocks * stat.f_frsize) / (1024 * 1024),
                'used_percent': ((stat.f_blocks - stat.f_bavail) / stat.f_blocks) * 100
            }
        except:
            diagnostics['storage_space'] = 'Unable to determine'
        
        return jsonify(diagnostics)
        
    except Exception as e:
        logger.error(f"Error in diagnostics: {e}")
        return jsonify({
            'error': 'Diagnostics failed',
            'details': str(e)
        }), 500