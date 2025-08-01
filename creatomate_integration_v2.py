"""
Creatomate API Integration v2 - Works with URLs
"""
import os
import logging
import requests
import time
from typing import List, Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class CreatomateAPI:
    """Handle all Creatomate API interactions"""
    
    def __init__(self):
        self.api_key = os.environ.get('CREATOMATE_API_KEY', '561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3')
        self.template_id = os.environ.get('CREATOMATE_TEMPLATE_ID', '5c2eca01-84b8-4302-bad2-9189db4dae70')
        self.base_url = 'https://api.creatomate.com/v1'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_render(self, 
                     image_urls: List[str],
                     property_details: Dict[str, str] = None) -> Optional[str]:
        """Create a render job with the real estate template"""
        
        # Default property details if not provided
        if property_details is None:
            property_details = {}
        
        # Build modifications object
        modifications = {}
        
        # Use example images if no URLs provided
        if not image_urls:
            image_urls = [
                "https://creatomate.com/files/assets/353ba980-9f13-4613-a8c5-f3aca0c41324",
                "https://creatomate.com/files/assets/f1cedfdd-eb93-4bda-a2f0-9171e3c71c41",
                "https://creatomate.com/files/assets/a2fc1725-f761-4d68-a6e8-001aa890c126",
                "https://creatomate.com/files/assets/cc72d7f3-ae1a-494e-af46-f080fa2c5d85",
                "https://creatomate.com/files/assets/9fc100e8-cbb5-451d-8c5e-d9f75b190cb1"
            ]
        
        # Add property photos (up to 5)
        for i, url in enumerate(image_urls[:5], 1):
            modifications[f'Photo-{i}.source'] = url
            # Try to set duration per photo (24 seconds each for 2-minute video)
            modifications[f'Photo-{i}.duration'] = 24
        
        # If less than 5 images, repeat the last one
        if len(image_urls) < 5:
            last_url = image_urls[-1]
            for i in range(len(image_urls) + 1, 6):
                modifications[f'Photo-{i}.source'] = last_url
                modifications[f'Photo-{i}.duration'] = 24
        
        # Add property details with defaults
        modifications.update({
            'Address.text': property_details.get('address', 'Beautiful Property\nYour City, State'),
            'Details-1.text': property_details.get('details1', '2,500 sqft\n3 Bedrooms\n2 Bathrooms'),
            'Details-2.text': property_details.get('details2', 'Modern Home\nMove-in Ready\nCall for Price'),
            'Name.text': property_details.get('agent_name', 'Your Real Estate Agent'),
            'Email.text': property_details.get('agent_email', 'agent@realestate.com'),
            'Phone-Number.text': property_details.get('agent_phone', '(555) 123-4567'),
            'Brand-Name.text': property_details.get('brand_name', 'Premium Real Estate'),
            'Picture.source': property_details.get('agent_photo', 'https://creatomate.com/files/assets/08322d05-9717-402a-b267-5f49fb511f95')
        })
        
        # Create render request
        render_data = {
            'template_id': self.template_id,
            'modifications': modifications,
            # Try to set custom duration (may or may not work with this template)
            'options': {
                'duration': 120  # Try 2 minutes instead of 1 minute
            }
        }
        
        try:
            logger.info("Creating Creatomate render...")
            response = requests.post(
                f'{self.base_url}/renders',
                headers=self.headers,
                json=render_data
            )
            
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"API returned status {response.status_code}: {response.text}")
            
            # Handle response - could be array or single object
            data = response.json()
            if isinstance(data, list):
                render_id = data[0]['id']
            else:
                render_id = data.get('id')
            
            logger.info(f"Render created with ID: {render_id}")
            return render_id
            
        except Exception as e:
            logger.error(f"Error creating render: {e}")
            return None
    
    def get_render_status(self, render_id: str) -> Tuple[str, Optional[str], Optional[int]]:
        """Check the status of a render job
        Returns: (status, url, progress_percentage)
        """
        try:
            response = requests.get(
                f'{self.base_url}/renders/{render_id}',
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            status = data.get('status', 'unknown')
            url = data.get('url')
            progress = data.get('progress', 0)
            
            return status, url, progress
            
        except Exception as e:
            logger.error(f"Error checking render status: {e}")
            return 'error', None, 0
    
    def wait_for_render(self, render_id: str, timeout: int = 300) -> Optional[str]:
        """Wait for a render to complete and return the video URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status, url, progress = self.get_render_status(render_id)
            
            if status == 'succeeded' and url:
                logger.info(f"Render completed successfully: {url}")
                return url
            elif status == 'failed':
                logger.error("Render failed")
                return None
            else:
                logger.info(f"Render progress: {progress}% - Status: {status}")
                time.sleep(2)  # Poll every 2 seconds
        
        logger.error("Render timeout")
        return None


def create_real_estate_video_from_urls(image_urls: List[str], 
                                      property_details: Optional[Dict[str, str]] = None,
                                      job_id: str = None) -> Optional[str]:
    """Create a real estate video using Creatomate with image URLs"""
    
    api = CreatomateAPI()
    
    # Create render
    render_id = api.create_render(image_urls, property_details)
    if not render_id:
        return None
    
    # Wait for completion
    video_url = api.wait_for_render(render_id)
    
    return video_url


def create_real_estate_video(image_paths: List[str], 
                           property_details: Optional[Dict[str, str]] = None,
                           job_id: str = None) -> Optional[str]:
    """Main function to create a real estate video with actual images"""
    
    # Upload images to Cloudinary first
    try:
        from cloudinary_integration import upload_to_cloudinary
        
        logger.info(f"Uploading {len(image_paths)} images to Cloudinary...")
        image_urls = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"Uploading image {i+1}/{len(image_paths)}...")
            try:
                cloudinary_url = upload_to_cloudinary(image_path, f"creatomate_{job_id}_{i}")
                if cloudinary_url:
                    image_urls.append(cloudinary_url)
                else:
                    logger.error(f"Failed to upload {image_path} to Cloudinary")
            except Exception as e:
                logger.error(f"Error uploading {image_path}: {e}")
        
        if not image_urls:
            logger.error("No images uploaded successfully to Cloudinary")
            return None
        
        logger.info(f"Successfully uploaded {len(image_urls)} images to Cloudinary")
        return create_real_estate_video_from_urls(image_urls, property_details, job_id)
        
    except ImportError:
        logger.error("Cloudinary integration not available")
        return None
    except Exception as e:
        logger.error(f"Error in create_real_estate_video: {e}")
        return None


# Export the v2 version
__all__ = ['CreatomateAPI', 'create_real_estate_video', 'create_real_estate_video_from_urls']