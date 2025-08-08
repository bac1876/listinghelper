"""
ImageKit integration using official SDK
Replaces Cloudinary to bypass 100MB limit and credit restrictions
"""
import os
import logging
import inspect
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Defensive imports to prevent crashes
ImageKit = None
UploadFileRequestOptions = None
imagekitio = None

try:
    logger.info("🔍 Starting ImageKit package import process...")
    
    # Check if packages are available
    logger.info("Checking for required packages...")
    import sys
    import pkg_resources
    
    # Log Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check for package dependencies
    required_packages = ['imagekitio', 'requests', 'requests-toolbelt', 'urllib3']
    for package in required_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            logger.info(f"✓ {package} version {version} is installed")
        except pkg_resources.DistributionNotFound:
            logger.error(f"✗ {package} is NOT installed")
        except Exception as e:
            logger.error(f"? Error checking {package}: {e}")
    
    logger.info("Attempting to import imagekitio package...")
    import imagekitio
    logger.info(f"✓ imagekitio package imported successfully, version: {getattr(imagekitio, '__version__', 'unknown')}")
    
    from imagekitio import ImageKit
    logger.info("✓ ImageKit class imported successfully")
    
    from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
    logger.info("✓ UploadFileRequestOptions imported successfully")
    
except ImportError as e:
    logger.error(f"✗ Failed to import imagekitio: {e}")
    logger.error("ImageKit functionality will be disabled")
except Exception as e:
    logger.error(f"✗ Unexpected error importing imagekitio: {e}")
    logger.error("ImageKit functionality will be disabled")

class ImageKitIntegration:
    def __init__(self):
        # Check if imports were successful
        if ImageKit is None:
            error_msg = "ImageKit SDK not available - import failed during module initialization"
            logger.error(error_msg)
            raise ImportError(error_msg)
        
        logger.info("Starting ImageKit initialization...")
        
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
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize ImageKit SDK
        self.imagekit = ImageKit(
            private_key=self.private_key,
            public_key=self.public_key,
            url_endpoint=self.url_endpoint
        )
        
        # Debug logging for SDK version and capabilities
        logger.info(f"ImageKit SDK initialized with endpoint: {self.url_endpoint}")
        logger.info(f"imagekitio package version: {getattr(imagekitio, '__version__', 'unknown')}")
        
        # Log upload_file method signature
        upload_sig = inspect.signature(self.imagekit.upload_file)
        logger.info(f"upload_file signature: {upload_sig}")
        
        # Log UploadFileRequestOptions signature  
        options_sig = inspect.signature(UploadFileRequestOptions.__init__)
        logger.info(f"UploadFileRequestOptions signature: {options_sig}")
    
    def upload_file(self, file_path: str, file_name: str, folder: str = "/tours/") -> Dict[str, Any]:
        """
        Upload a file to ImageKit using the official SDK
        
        Args:
            file_path: Path to the file to upload
            file_name: Name for the file in ImageKit
            folder: Folder path in ImageKit (default: /tours/)
            
        Returns:
            Dict with upload response including URL
        """
        try:
            logger.info(f"Uploading {file_name} to ImageKit folder {folder}")
            
            # Use the simplest approach that works
            with open(file_path, "rb") as file_obj:
                if UploadFileRequestOptions is not None and folder != "/tours/":
                    # Use folder option if available and needed
                    options = UploadFileRequestOptions(
                        folder=folder,
                        use_unique_file_name=False
                    )
                    result = self.imagekit.upload_file(
                        file=file_obj,
                        file_name=file_name,
                        options=options
                    )
                else:
                    # Simple upload without folder
                    result = self.imagekit.upload_file(
                        file=file_obj,
                        file_name=file_name
                    )
            
            # Check if upload was successful - SDK returns UploadFileResult object
            logger.info(f"Upload result type: {type(result)}")
            
            # The SDK always returns an UploadFileResult object
            if result and hasattr(result, 'url') and result.url:
                logger.info(f"Successfully uploaded to ImageKit: {result.url}")
                return {
                    'success': True,
                    'url': result.url,
                    'fileId': getattr(result, 'file_id', ''),
                    'name': getattr(result, 'name', ''),
                    'size': getattr(result, 'size', 0)
                }
            else:
                # If no URL, the upload failed
                error_msg = "Upload failed - no URL returned from ImageKit"
                logger.error(f"{error_msg}. Result object: {result}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"Error uploading to ImageKit: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_from_url(self, source_url: str, file_name: str, folder: str = "/tours/") -> Dict[str, Any]:
        """
        Upload a file to ImageKit from a URL using the official SDK
        
        Args:
            source_url: URL of the file to upload
            file_name: Name for the file in ImageKit
            folder: Folder path in ImageKit
            
        Returns:
            Dict with upload response
        """
        try:
            logger.info(f"Uploading from URL {source_url} to ImageKit")
            
            # Create options object  
            if UploadFileRequestOptions is None:
                raise ImportError("UploadFileRequestOptions not available")
                
            options = UploadFileRequestOptions(
                folder=folder,
                use_unique_file_name=False
            )
            
            result = self.imagekit.upload_file(
                file=source_url,
                file_name=file_name,
                options=options
            )
            
            # Check if upload was successful - SDK returns UploadFileResult object
            if result and hasattr(result, 'url') and result.url:
                logger.info(f"Successfully uploaded from URL to ImageKit: {result.url}")
                return {
                    'success': True,
                    'url': result.url,
                    'fileId': getattr(result, 'file_id', '')
                }
            else:
                error_msg = "Upload from URL failed - no URL returned"
                logger.error(f"{error_msg}. Result object: {result}")
                return {
                    'success': False,
                    'error': error_msg
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
        Delete a file from ImageKit using the official SDK
        
        Args:
            file_id: ImageKit file ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.imagekit.delete_file(file_id)
            return True
            
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
            logger.info("Attempting to create ImageKitIntegration instance...")
            _imagekit_instance = ImageKitIntegration()
            logger.info("✓ ImageKit successfully initialized")
        except ImportError as e:
            logger.error(f"✗ ImageKit SDK import failed: {e}")
            logger.error("ImageKit functionality completely disabled due to import failure")
            return None
        except ValueError as e:
            logger.error(f"✗ ImageKit configuration error: {e}")
            logger.error("ImageKit credentials missing or invalid")
            return None
        except Exception as e:
            logger.error(f"✗ Unexpected ImageKit initialization error: {e}")
            logger.error("ImageKit functionality disabled due to unknown error")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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