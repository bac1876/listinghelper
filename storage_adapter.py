"""
Storage adapter that allows switching between ImageKit and Bunny.net
This provides a unified interface regardless of which service is being used
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StorageAdapter:
    def __init__(self):
        """Initialize storage adapter with appropriate backend"""
        self.backend = None
        self.backend_name = None
        
        # Check which service to use based on environment variables
        use_bunnynet = os.environ.get('USE_BUNNYNET', 'false').lower() == 'true'
        
        # Try Bunny.net first if enabled
        if use_bunnynet or os.environ.get('BUNNY_ACCESS_KEY'):
            try:
                from bunnynet_integration import get_bunnynet, test_bunnynet_initialization
                if test_bunnynet_initialization():
                    self.backend = get_bunnynet()
                    self.backend_name = 'bunnynet'
                    logger.info("✓ Using Bunny.net for storage")
                else:
                    logger.error("Bunny.net initialization failed")
            except Exception as e:
                logger.warning(f"Could not initialize Bunny.net: {e}")
        
        # Only use Bunny.net - ImageKit has been removed due to transformation limits
        if self.backend is None:
            raise RuntimeError("No storage backend available! Please configure Bunny.net with BUNNY_ACCESS_KEY, BUNNY_STORAGE_ZONE_NAME, and BUNNY_PULL_ZONE_URL.")
    
    def upload_file(self, file_path: str, file_name: str, folder: str = "tours/") -> Dict[str, Any]:
        """Upload a file using the configured backend"""
        if self.backend_name == 'bunnynet':
            # Bunny.net expects folder without leading slash
            folder = folder.lstrip('/')
        elif self.backend_name == 'imagekit':
            # ImageKit expects folder with leading slash
            if not folder.startswith('/'):
                folder = '/' + folder
        
        return self.backend.upload_file(file_path, file_name, folder)
    
    def upload_from_url(self, source_url: str, file_name: str, folder: str = "tours/") -> Dict[str, Any]:
        """Upload from URL using the configured backend"""
        if self.backend_name == 'bunnynet':
            folder = folder.lstrip('/')
        elif self.backend_name == 'imagekit':
            if not folder.startswith('/'):
                folder = '/' + folder
        
        return self.backend.upload_from_url(source_url, file_name, folder)
    
    def get_video_url(self, file_name: str, folder: str = "tours/") -> str:
        """Get video URL using the configured backend"""
        if self.backend_name == 'bunnynet':
            folder = folder.lstrip('/')
        elif self.backend_name == 'imagekit':
            if not folder.startswith('/'):
                folder = '/' + folder
        
        return self.backend.get_video_url(file_name, folder)
    
    def delete_file(self, file_id_or_path: str) -> bool:
        """Delete a file using the configured backend"""
        if self.backend_name == 'bunnynet':
            # Bunny.net uses file path
            return self.backend.delete_file(file_id_or_path)
        elif self.backend_name == 'imagekit':
            # ImageKit uses file ID
            return self.backend.delete_file(file_id_or_path)
        return False
    
    def get_backend_name(self) -> str:
        """Get the name of the current backend"""
        return self.backend_name

# Singleton instance
_storage_instance = None

def get_storage():
    """Get or create storage adapter instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = StorageAdapter()
    return _storage_instance

def test_storage_initialization():
    """Test storage initialization and return backend info"""
    try:
        storage = get_storage()
        logger.info(f"Storage adapter initialized with backend: {storage.get_backend_name()}")
        return True, storage.get_backend_name()
    except Exception as e:
        logger.error(f"Storage adapter initialization failed: {e}")
        return False, None