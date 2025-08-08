"""
Upload files to ImageKit (replacement for Cloudinary)
No size limits, better free tier
"""
import os
import logging
from typing import List, Optional
from imagekit_integration import imagekit

logger = logging.getLogger(__name__)

def upload_files_to_imagekit(file_paths: List[str], folder: str = "/tours/temp/") -> List[str]:
    """
    Upload multiple files to ImageKit
    
    Args:
        file_paths: List of local file paths to upload
        folder: ImageKit folder (default: /tours/temp/)
        
    Returns:
        List of ImageKit URLs for the uploaded files
    """
    if not imagekit:
        logger.error("ImageKit not configured")
        return []
    
    uploaded_urls = []
    
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                continue
            
            # Get filename
            file_name = os.path.basename(file_path)
            
            # Upload to ImageKit
            logger.info(f"Uploading {file_name} to ImageKit...")
            result = imagekit.upload_file(file_path, file_name, folder)
            
            if result.get('success'):
                url = result.get('url')
                logger.info(f"Successfully uploaded to ImageKit: {url}")
                uploaded_urls.append(url)
            else:
                logger.error(f"Failed to upload {file_name}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error uploading {file_path} to ImageKit: {e}")
    
    return uploaded_urls

def upload_video_to_imagekit(video_path: str, job_id: str) -> Optional[str]:
    """
    Upload a video to ImageKit with a specific job ID
    
    Args:
        video_path: Path to the video file
        job_id: Unique job identifier
        
    Returns:
        ImageKit URL of the uploaded video, or None if failed
    """
    if not imagekit:
        logger.error("ImageKit not configured")
        return None
    
    try:
        # Use job ID as filename for easy retrieval
        file_name = f"{job_id}.mp4"
        
        logger.info(f"Uploading video {file_name} to ImageKit...")
        result = imagekit.upload_file(video_path, file_name, "/tours/videos/")
        
        if result.get('success'):
            url = result.get('url')
            logger.info(f"Video uploaded successfully to ImageKit: {url}")
            return url
        else:
            logger.error(f"Failed to upload video: {result.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading video to ImageKit: {e}")
        return None

def get_video_url_imagekit(job_id: str) -> str:
    """
    Get the ImageKit URL for a video by job ID
    
    Args:
        job_id: The job identifier
        
    Returns:
        ImageKit URL for the video
    """
    if not imagekit:
        return ""
    
    return imagekit.get_video_url(f"{job_id}.mp4", "/tours/videos/")