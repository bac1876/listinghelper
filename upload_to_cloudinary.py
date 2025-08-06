import cloudinary
import cloudinary.uploader
import os
import logging

logger = logging.getLogger(__name__)

def upload_files_to_cloudinary(file_paths):
    """
    Upload local files to Cloudinary and return their URLs
    
    Args:
        file_paths: List of local file paths
        
    Returns:
        List of Cloudinary URLs
    """
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
    
    uploaded_urls = []
    
    for file_path in file_paths:
        try:
            # Upload image to Cloudinary with optimizations
            result = cloudinary.uploader.upload(
                file_path,
                folder="tours/temp",
                resource_type="image",
                quality="auto:good",
                fetch_format="auto",
                transformation=[
                    {'width': 1920, 'height': 1080, 'crop': 'limit'},  # Max Full HD
                    {'quality': 'auto:good'},  # Auto quality optimization
                    {'fetch_format': 'auto'}  # Auto format (WebP where supported)
                ]
            )
            
            uploaded_urls.append(result['secure_url'])
            logger.info(f"Uploaded {file_path} to Cloudinary: {result['secure_url']}")
            
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to Cloudinary: {e}")
            # Continue with other files even if one fails
            
    return uploaded_urls