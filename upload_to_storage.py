"""
Upload files to storage backend (Bunny.net or ImageKit)
This replaces the upload_to_imagekit.py module
"""
import os
import logging
from typing import List, Optional
from storage_adapter import get_storage

logger = logging.getLogger(__name__)

def upload_files_to_storage(file_paths: List[str], folder: str = "tours/temp/") -> List[str]:
    """
    Upload multiple files to storage backend
    
    Args:
        file_paths: List of local file paths to upload
        folder: Storage folder (default: tours/temp/)
        
    Returns:
        List of CDN URLs for the uploaded files
    """
    try:
        logger.info("Getting storage backend instance...")
        storage = get_storage()
        backend_name = storage.get_backend_name()
        logger.info(f"Using {backend_name} for file uploads")
    except Exception as e:
        logger.error(f"Failed to get storage instance: {e}")
        return []
    
    uploaded_urls = []
    
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                continue
            
            # Get filename
            file_name = os.path.basename(file_path)
            
            # Upload to storage
            logger.info(f"Uploading {file_name} to {backend_name}...")
            result = storage.upload_file(file_path, file_name, folder)
            
            if result.get('success'):
                url = result.get('url')
                logger.info(f"Successfully uploaded: {url}")
                uploaded_urls.append(url)
            else:
                logger.error(f"Failed to upload {file_name}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {e}")
    
    logger.info(f"Uploaded {len(uploaded_urls)}/{len(file_paths)} files successfully")
    return uploaded_urls

def upload_video_to_storage(video_path: str, video_name: Optional[str] = None, folder: str = "tours/videos/") -> Optional[str]:
    """
    Upload a video file to storage backend
    
    Args:
        video_path: Local path to the video file
        video_name: Optional custom name for the video
        folder: Storage folder for videos
        
    Returns:
        CDN URL of the uploaded video or None if failed
    """
    try:
        storage = get_storage()
        backend_name = storage.get_backend_name()
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
        
        # Use provided name or get from file path
        if not video_name:
            video_name = os.path.basename(video_path)
        
        logger.info(f"Uploading video {video_name} to {backend_name}...")
        
        result = storage.upload_file(video_path, video_name, folder)
        
        if result.get('success'):
            url = result.get('url')
            logger.info(f"Video uploaded successfully: {url}")
            return url
        else:
            logger.error(f"Failed to upload video: {result.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        return None

def get_video_url_storage(video_name: str, folder: str = "tours/videos/") -> str:
    """
    Get the CDN URL for a video in storage
    
    Args:
        video_name: Name of the video file
        folder: Folder path in storage
        
    Returns:
        Full CDN URL to the video
    """
    try:
        storage = get_storage()
        return storage.get_video_url(video_name, folder)
    except Exception as e:
        logger.error(f"Error getting video URL: {e}")
        return ""

# Compatibility aliases for existing code
upload_files_to_imagekit = upload_files_to_storage
upload_video_to_imagekit = upload_video_to_storage
get_video_url_imagekit = get_video_url_storage