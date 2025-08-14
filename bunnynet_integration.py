"""
Bunny.net Storage integration for video and image uploads
Replaces ImageKit to avoid video transformation limits
"""
import os
import logging
import requests
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class BunnyNetIntegration:
    def __init__(self):
        """Initialize Bunny.net Storage integration"""
        logger.info("Starting Bunny.net initialization...")
        
        # Get configuration from environment variables
        self.storage_zone_name = os.environ.get('BUNNY_STORAGE_ZONE_NAME')
        self.access_key = os.environ.get('BUNNY_ACCESS_KEY')
        self.pull_zone_url = os.environ.get('BUNNY_PULL_ZONE_URL')
        self.region = os.environ.get('BUNNY_REGION', '')  # Empty string for main region
        
        # Validate required configuration
        missing = []
        if not self.storage_zone_name:
            missing.append('BUNNY_STORAGE_ZONE_NAME')
        if not self.access_key:
            missing.append('BUNNY_ACCESS_KEY')
        if not self.pull_zone_url:
            missing.append('BUNNY_PULL_ZONE_URL')
            
        if missing:
            error_msg = f"Missing Bunny.net credentials: {', '.join(missing)}. Please set these environment variables."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Construct base URL for storage API
        base_url = "storage.bunnycdn.com"
        if self.region:
            base_url = f"{self.region}.{base_url}"
        self.storage_api_url = f"https://{base_url}/{self.storage_zone_name}"
        
        # Ensure pull zone URL has proper format
        if not self.pull_zone_url.startswith('http'):
            self.pull_zone_url = f"https://{self.pull_zone_url}"
        if not self.pull_zone_url.endswith('/'):
            self.pull_zone_url += '/'
            
        logger.info(f"Bunny.net initialized with storage zone: {self.storage_zone_name}")
        logger.info(f"Storage API URL: {self.storage_api_url}")
        logger.info(f"Pull Zone URL: {self.pull_zone_url}")
    
    def upload_file(self, file_path: str, file_name: str, folder: str = "tours/") -> Dict[str, Any]:
        """
        Upload a file to Bunny.net Storage
        
        Args:
            file_path: Path to the file to upload
            file_name: Name for the file in Bunny.net
            folder: Folder path in Bunny.net (default: tours/)
            
        Returns:
            Dict with upload response including URL
        """
        try:
            # Ensure folder format (no leading slash, with trailing slash)
            folder = folder.lstrip('/').rstrip('/') + '/' if folder else ''
            
            # Construct the full path in storage
            storage_path = f"{folder}{file_name}"
            
            # Full URL for the upload
            upload_url = f"{self.storage_api_url}/{storage_path}"
            
            logger.info(f"Uploading {file_name} to Bunny.net at {storage_path}")
            
            headers = {
                "AccessKey": self.access_key,
                "Content-Type": "application/octet-stream",
                "accept": "application/json"
            }
            
            # Upload the file
            with open(file_path, 'rb') as file_data:
                response = requests.put(upload_url, headers=headers, data=file_data)
            
            # Check response
            if response.status_code in [200, 201]:
                # Construct the CDN URL
                cdn_url = f"{self.pull_zone_url}{storage_path}"
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                logger.info(f"Successfully uploaded to Bunny.net: {cdn_url}")
                return {
                    'success': True,
                    'url': cdn_url,
                    'storage_path': storage_path,
                    'size': file_size,
                    'name': file_name
                }
            else:
                error_msg = f"Upload failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error uploading to Bunny.net: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_from_url(self, source_url: str, file_name: str, folder: str = "tours/") -> Dict[str, Any]:
        """
        Upload a file to Bunny.net from a URL
        
        Args:
            source_url: URL of the file to upload
            file_name: Name for the file in Bunny.net
            folder: Folder path in Bunny.net
            
        Returns:
            Dict with upload response
        """
        try:
            logger.info(f"Downloading from URL {source_url} for upload to Bunny.net")
            
            # Download the file first
            response = requests.get(source_url, stream=True)
            if response.status_code != 200:
                raise Exception(f"Failed to download from URL: {response.status_code}")
            
            # Ensure folder format
            folder = folder.lstrip('/').rstrip('/') + '/' if folder else ''
            storage_path = f"{folder}{file_name}"
            upload_url = f"{self.storage_api_url}/{storage_path}"
            
            headers = {
                "AccessKey": self.access_key,
                "Content-Type": "application/octet-stream",
                "accept": "application/json"
            }
            
            # Upload the content directly from the download
            upload_response = requests.put(upload_url, headers=headers, data=response.content)
            
            if upload_response.status_code in [200, 201]:
                cdn_url = f"{self.pull_zone_url}{storage_path}"
                logger.info(f"Successfully uploaded from URL to Bunny.net: {cdn_url}")
                return {
                    'success': True,
                    'url': cdn_url,
                    'storage_path': storage_path,
                    'name': file_name
                }
            else:
                error_msg = f"Upload from URL failed: {upload_response.status_code}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error uploading URL to Bunny.net: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_video_url(self, file_name: str, folder: str = "tours/") -> str:
        """
        Get the CDN URL for a video in Bunny.net
        
        Args:
            file_name: Name of the file
            folder: Folder path (default: tours/)
            
        Returns:
            Full CDN URL to the video
        """
        # Ensure folder format
        folder = folder.lstrip('/').rstrip('/') + '/' if folder else ''
        
        # Construct CDN URL
        url = f"{self.pull_zone_url}{folder}{file_name}"
        return url
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Bunny.net Storage
        
        Args:
            file_path: Path to the file in storage (e.g., "tours/video.mp4")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure no leading slash
            file_path = file_path.lstrip('/')
            
            delete_url = f"{self.storage_api_url}/{file_path}"
            
            headers = {
                "AccessKey": self.access_key,
                "accept": "application/json"
            }
            
            response = requests.delete(delete_url, headers=headers)
            
            if response.status_code in [200, 404]:  # 404 is OK (file already deleted)
                logger.info(f"Deleted from Bunny.net: {file_path}")
                return True
            else:
                logger.error(f"Failed to delete from Bunny.net: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting from Bunny.net: {e}")
            return False
    
    def list_files(self, folder: str = "") -> Optional[list]:
        """
        List files in a Bunny.net Storage folder
        
        Args:
            folder: Folder path to list (empty for root)
            
        Returns:
            List of files or None on error
        """
        try:
            # Ensure folder format
            folder = folder.lstrip('/').rstrip('/')
            
            list_url = f"{self.storage_api_url}/{folder}/"
            
            headers = {
                "AccessKey": self.access_key,
                "accept": "application/json"
            }
            
            response = requests.get(list_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to list files: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error listing files from Bunny.net: {e}")
            return None

# Lazy initialization - will be initialized when first used
_bunnynet_instance = None

def get_bunnynet():
    """Get or create BunnyNet instance with lazy initialization"""
    global _bunnynet_instance
    if _bunnynet_instance is None:
        # Debug: Log which environment variables are present
        storage_zone = os.environ.get('BUNNY_STORAGE_ZONE_NAME')
        access_key = os.environ.get('BUNNY_ACCESS_KEY')
        pull_zone = os.environ.get('BUNNY_PULL_ZONE_URL')
        
        logger.info("Bunny.net environment check:")
        logger.info(f"  BUNNY_STORAGE_ZONE_NAME: {'SET' if storage_zone else 'NOT SET'}")
        logger.info(f"  BUNNY_ACCESS_KEY: {'SET' if access_key else 'NOT SET'}")
        logger.info(f"  BUNNY_PULL_ZONE_URL: {pull_zone if pull_zone else 'NOT SET'}")
        
        if access_key:
            logger.info(f"  Access key starts with: {access_key[:10]}...")
            
        try:
            logger.info("Attempting to create BunnyNetIntegration instance...")
            _bunnynet_instance = BunnyNetIntegration()
            logger.info("✓ Bunny.net successfully initialized")
        except ValueError as e:
            logger.error(f"✗ Bunny.net configuration error: {e}")
            logger.error("Bunny.net credentials missing or invalid")
            return None
        except Exception as e:
            logger.error(f"✗ Unexpected Bunny.net initialization error: {e}")
            logger.error("Bunny.net functionality disabled due to unknown error")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    return _bunnynet_instance

# For backward compatibility with ImageKit interface
class LazyBunnyNet:
    @property
    def instance(self):
        return get_bunnynet()
    
    def __getattr__(self, name):
        instance = self.instance
        if instance is None:
            raise RuntimeError("Bunny.net not configured. Please set BUNNY_STORAGE_ZONE_NAME, BUNNY_ACCESS_KEY, and BUNNY_PULL_ZONE_URL")
        return getattr(instance, name)

bunnynet = LazyBunnyNet()

def test_bunnynet_initialization():
    """Test Bunny.net initialization and return status"""
    logger.info("Testing Bunny.net initialization...")
    
    # Check environment variables
    env_vars = {
        'BUNNY_STORAGE_ZONE_NAME': os.environ.get('BUNNY_STORAGE_ZONE_NAME'),
        'BUNNY_ACCESS_KEY': os.environ.get('BUNNY_ACCESS_KEY'),
        'BUNNY_PULL_ZONE_URL': os.environ.get('BUNNY_PULL_ZONE_URL'),
        'BUNNY_REGION': os.environ.get('BUNNY_REGION', 'default')
    }
    
    logger.info("Environment variables check:")
    for key, value in env_vars.items():
        if value:
            # Mask sensitive parts but show enough to verify format
            if 'ACCESS_KEY' in key:
                masked = f"{value[:15]}..." if len(value) > 15 else "TOO_SHORT"
            else:
                masked = value  # Zone names and URLs are not sensitive
            logger.info(f"  {key}: {masked}")
        else:
            logger.error(f"  {key}: NOT SET")
    
    # Try to initialize
    instance = get_bunnynet()
    if instance:
        logger.info("✓ Bunny.net initialization successful!")
        return True
    else:
        logger.error("✗ Bunny.net initialization failed!")
        return False