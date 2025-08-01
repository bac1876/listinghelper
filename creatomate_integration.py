"""
Creatomate API Integration for Professional Real Estate Videos
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
        
    def upload_image(self, image_path: str) -> Optional[str]:
        """Upload an image to Creatomate and return the asset URL"""
        try:
            # First, create an upload URL
            upload_response = requests.post(
                f'{self.base_url}/assets',
                headers=self.headers,
                json={
                    'filename': os.path.basename(image_path),
                    'type': 'image'
                }
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()
            
            # Upload the file to the provided URL
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
                upload_result = requests.post(
                    upload_data['upload_url'],
                    files=files
                )
                upload_result.raise_for_status()
            
            # Return the asset URL
            asset_url = upload_data.get('url')
            logger.info(f"Uploaded {os.path.basename(image_path)} to Creatomate: {asset_url}")
            return asset_url
            
        except Exception as e:
            logger.error(f"Error uploading image {image_path}: {e}")
            return None
    
    def create_render(self, 
                     image_paths_or_urls: List[str],
                     property_details: Dict[str, str] = None) -> Optional[str]:
        """Create a render job with the real estate template"""
        
        # Default property details if not provided
        if property_details is None:
            property_details = {
                'address': 'Beautiful Property\nYour City, State',
                'details1': '2,500 sqft\n3 Bedrooms\n2 Bathrooms',
                'details2': 'Modern Home\nMove-in Ready\nCall for Price',
                'agent_name': 'Your Real Estate Agent',
                'agent_email': 'agent@realestate.com',
                'agent_phone': '(555) 123-4567',
                'brand_name': 'Premium Real Estate',
                'agent_photo': 'https://creatomate.com/files/assets/08322d05-9717-402a-b267-5f49fb511f95'
            }
        
        # Build modifications object
        modifications = {}
        
        # Add property photos (up to 5)
        for i, url in enumerate(image_paths_or_urls[:5], 1):
            modifications[f'Photo-{i}.source'] = url
        
        # If less than 5 images, repeat the last one
        if len(image_paths_or_urls) < 5:
            last_url = image_paths_or_urls[-1]
            for i in range(len(image_paths_or_urls) + 1, 6):
                modifications[f'Photo-{i}.source'] = last_url
        
        # Add property details
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
            'modifications': modifications
        }
        
        try:
            logger.info("Creating Creatomate render...")
            response = requests.post(
                f'{self.base_url}/renders',
                headers=self.headers,
                json=render_data
            )
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"API returned status {response.status_code}")
            
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
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
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


def create_real_estate_video(image_paths: List[str], 
                           property_details: Optional[Dict[str, str]] = None,
                           job_id: str = None) -> Optional[str]:
    """Main function to create a real estate video using Creatomate"""
    
    api = CreatomateAPI()
    
    # Upload all images
    logger.info(f"Uploading {len(image_paths)} images to Creatomate...")
    image_urls = []
    
    for i, image_path in enumerate(image_paths):
        logger.info(f"Uploading image {i+1}/{len(image_paths)}...")
        url = api.upload_image(image_path)
        if url:
            image_urls.append(url)
        else:
            logger.error(f"Failed to upload {image_path}")
    
    if not image_urls:
        logger.error("No images uploaded successfully")
        return None
    
    # Create render
    render_id = api.create_render(image_urls, property_details)
    if not render_id:
        return None
    
    # Wait for completion
    video_url = api.wait_for_render(render_id)
    
    return video_url


# Test function
if __name__ == "__main__":
    # Test with sample images
    import glob
    test_images = glob.glob("test_images/*.jpg")[:3]
    
    if test_images:
        print("Testing Creatomate integration...")
        result = create_real_estate_video(
            test_images,
            {
                'address': 'Test Property\nLos Angeles, CA',
                'details1': '1,500 sqft\n2 Bedrooms\n1 Bathroom',
                'details2': 'Built in 2020\n1 Garage\n$750,000'
            }
        )
        if result:
            print(f"Success! Video URL: {result}")
        else:
            print("Failed to create video")
    else:
        print("No test images found")