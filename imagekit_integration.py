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
        
        # Debug logging
        missing = []
        if not self.private_key:
            missing.append('IMAGEKIT_PRIVATE_KEY')
        if not self.public_key:
            missing.append('IMAGEKIT_PUBLIC_KEY')
        if not self.url_endpoint:
            missing.append('IMAGEKIT_URL_ENDPOINT')
            
        if missing:
            error_msg = f"Missing ImageKit credentials: {', '.join(missing)}. Please set these environment variables."
            raise ValueError(error_msg)
        
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
            
            # Determine MIME type based on file extension
            mime_type = 'image/jpeg'  # Default
            if file_name.lower().endswith('.mp4'):
                mime_type = 'video/mp4'
            elif file_name.lower().endswith('.png'):
                mime_type = 'image/png'
            elif file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif file_name.lower().endswith('.gif'):
                mime_type = 'image/gif'
            elif file_name.lower().endswith('.webp'):
                mime_type = 'image/webp'
            
            # Prepare upload data with proper data URI format
            upload_data = {
                'file': f'data:{mime_type};base64,{file_base64}',
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
        # Debug: Log which environment variables are present
        private_key = os.environ.get('IMAGEKIT_PRIVATE_KEY')
        public_key = os.environ.get('IMAGEKIT_PUBLIC_KEY')
        url_endpoint = os.environ.get('IMAGEKIT_URL_ENDPOINT')
        
        logger.info("ImageKit environment check:")
        logger.info(f"  IMAGEKIT_PRIVATE_KEY: {'SET' if private_key else 'NOT SET'}")
        logger.info(f"  IMAGEKIT_PUBLIC_KEY: {'SET' if public_key else 'NOT SET'}")
        logger.info(f"  IMAGEKIT_URL_ENDPOINT: {url_endpoint if url_endpoint else 'NOT SET'}")
        
        if private_key:
            logger.info(f"  Private key starts with: {private_key[:10]}...")
        if public_key:
            logger.info(f"  Public key starts with: {public_key[:10]}...")
            
        try:
            _imagekit_instance = ImageKitIntegration()
            logger.info("ImageKit successfully initialized")
        except Exception as e:
            logger.warning(f"ImageKit not configured: {e}")
            logger.warning("ImageKit initialization failed - will use Cloudinary as fallback")
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

def test_imagekit_initialization():
    """Test ImageKit initialization and return status"""
    logger.info("Testing ImageKit initialization...")
    
    # Check environment variables
    env_vars = {
        'IMAGEKIT_PRIVATE_KEY': os.environ.get('IMAGEKIT_PRIVATE_KEY'),
        'IMAGEKIT_PUBLIC_KEY': os.environ.get('IMAGEKIT_PUBLIC_KEY'),
        'IMAGEKIT_URL_ENDPOINT': os.environ.get('IMAGEKIT_URL_ENDPOINT')
    }
    
    logger.info("Environment variables check:")
    for key, value in env_vars.items():
        if value:
            # Mask sensitive parts but show enough to verify format
            if 'PRIVATE' in key:
                masked = f"{value[:15]}..." if len(value) > 15 else "TOO_SHORT"
            elif 'PUBLIC' in key:
                masked = f"{value[:15]}..." if len(value) > 15 else "TOO_SHORT"
            else:
                masked = value  # URL endpoint is not sensitive
            logger.info(f"  {key}: {masked}")
        else:
            logger.error(f"  {key}: NOT SET")
    
    # Try to initialize
    instance = get_imagekit()
    if instance:
        logger.info("✓ ImageKit initialization successful!")
        return True
    else:
        logger.error("✗ ImageKit initialization failed!")
        return False