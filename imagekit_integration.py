"""
ImageKit integration for video storage and delivery
Replaces Cloudinary to bypass 100MB limit and credit restrictions
"""
import os
import logging
from typing import Optional, Dict, Any
import requests
import base64

logger = logging.getLogger(__name__)

class ImageKitIntegration:
    def __init__(self):
        self.private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
        self.public_key = os.environ.get('IMAGEKIT_PUBLIC_KEY')
        self.url_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')
        
        if not all([self.private_key, self.public_key, self.url_endpoint]):
            raise ValueError("Missing ImageKit credentials. Please set IMAGEKIT_PRIVATE_KEY, IMAGEKIT_PUBLIC_KEY, and IMAGEKIT_URL_ENDPOINT")
        
        # ImageKit API endpoint
        self.api_base = "https://upload.imagekit.io/api/v1"
        
        # Create auth header (private key needs to be base64 encoded with colon)
        auth_string = f"{self.private_key}:"
        self.auth_header = base64.b64encode(auth_string.encode()).decode()
        
        logger.info(f"ImageKit integration initialized with endpoint: {self.url_endpoint}")
    
    def upload_file(self, file_path: str, file_name: str, folder: str = "/tours/") -> Dict[str, Any]:
        """
        Upload a file to ImageKit
        
        Args:
            file_path: Path to the file to upload
            file_name: Name for the file in ImageKit
            folder: Folder path in ImageKit (default: /tours/)
            
        Returns:
            Dict with upload response including URL
        """
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Encode to base64
            file_base64 = base64.b64encode(file_data).decode()
            
            # Prepare upload data
            upload_data = {
                'file': f'data:video/mp4;base64,{file_base64}' if file_name.endswith('.mp4') else file_base64,
                'fileName': file_name,
                'folder': folder,
                'useUniqueFileName': False  # Use our job ID as filename
            }
            
            # Headers
            headers = {
                'Authorization': f'Basic {self.auth_header}'
            }
            
            # Upload to ImageKit
            logger.info(f"Uploading {file_name} to ImageKit folder {folder}")
            response = requests.post(
                f"{self.api_base}/files/upload",
                json=upload_data,
                headers=headers,
                timeout=300  # 5 minute timeout for large videos
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully uploaded to ImageKit: {result.get('url')}")
                return {
                    'success': True,
                    'url': result.get('url'),
                    'fileId': result.get('fileId'),
                    'name': result.get('name'),
                    'size': result.get('size')
                }
            else:
                logger.error(f"ImageKit upload failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"Upload failed: {response.status_code}",
                    'details': response.text
                }
                
        except Exception as e:
            logger.error(f"Error uploading to ImageKit: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_from_url(self, source_url: str, file_name: str, folder: str = "/tours/") -> Dict[str, Any]:
        """
        Upload a file to ImageKit from a URL
        
        Args:
            source_url: URL of the file to upload
            file_name: Name for the file in ImageKit
            folder: Folder path in ImageKit
            
        Returns:
            Dict with upload response
        """
        try:
            upload_data = {
                'file': source_url,
                'fileName': file_name,
                'folder': folder,
                'useUniqueFileName': False
            }
            
            headers = {
                'Authorization': f'Basic {self.auth_header}'
            }
            
            logger.info(f"Uploading from URL {source_url} to ImageKit")
            response = requests.post(
                f"{self.api_base}/files/upload",
                json=upload_data,
                headers=headers,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Successfully uploaded from URL to ImageKit: {result.get('url')}")
                return {
                    'success': True,
                    'url': result.get('url'),
                    'fileId': result.get('fileId')
                }
            else:
                logger.error(f"ImageKit URL upload failed: {response.status_code}")
                return {
                    'success': False,
                    'error': f"Upload failed: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error uploading URL to ImageKit: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_video_url(self, file_name: str, folder: str = "/tours/") -> str:
        """
        Get the URL for a video in ImageKit
        
        Args:
            file_name: Name of the file
            folder: Folder path (default: /tours/)
            
        Returns:
            Full URL to the video
        """
        # Remove leading slash from folder if present
        folder = folder.lstrip('/')
        # Ensure trailing slash
        if not folder.endswith('/'):
            folder += '/'
        
        # Construct URL
        url = f"{self.url_endpoint}{folder}{file_name}"
        return url
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from ImageKit
        
        Args:
            file_id: ImageKit file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = {
                'Authorization': f'Basic {self.auth_header}'
            }
            
            response = requests.delete(
                f"{self.api_base}/files/{file_id}",
                headers=headers
            )
            
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Error deleting from ImageKit: {e}")
            return False

# Lazy initialization - will be initialized when first used
_imagekit_instance = None

def get_imagekit():
    """Get or create ImageKit instance with lazy initialization"""
    global _imagekit_instance
    if _imagekit_instance is None:
        try:
            _imagekit_instance = ImageKitIntegration()
            logger.info("ImageKit successfully initialized")
        except Exception as e:
            logger.warning(f"ImageKit not configured: {e}")
            return None
    return _imagekit_instance

# For backward compatibility, create a property that initializes on first access
class LazyImageKit:
    @property
    def instance(self):
        return get_imagekit()
    
    def __getattr__(self, name):
        instance = self.instance
        if instance is None:
            raise RuntimeError("ImageKit not configured. Please set IMAGEKIT_PRIVATE_KEY, IMAGEKIT_PUBLIC_KEY, and IMAGEKIT_URL_ENDPOINT")
        return getattr(instance, name)

imagekit = LazyImageKit()