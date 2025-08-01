"""
Remotion Integration for Real Estate Virtual Tours
Provides an alternative to Creatomate with full control over Ken Burns effects
"""
import os
import json
import subprocess
import logging
import tempfile
import shutil
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class RemotionVideoGenerator:
    """Generate videos using Remotion with custom Ken Burns effects"""
    
    def __init__(self):
        self.remotion_dir = os.path.join(os.path.dirname(__file__), 'remotion-tours')
        self.output_dir = os.path.join(self.remotion_dir, 'out')
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_video(self, 
                      image_paths: List[str], 
                      property_details: Dict[str, str],
                      settings: Optional[Dict[str, any]] = None,
                      job_id: str = None) -> Optional[str]:
        """
        Generate a video using Remotion with custom Ken Burns effects
        
        Args:
            image_paths: List of local image file paths
            property_details: Dictionary with property information
            settings: Optional settings for timing and effects
            job_id: Unique job identifier
            
        Returns:
            Path to generated video or None if failed
        """
        
        if not image_paths:
            logger.error("No images provided")
            return None
        
        # Default settings
        if settings is None:
            settings = {
                'durationPerImage': 8,  # 8 seconds per image
                'effectSpeed': 'medium',  # slow, medium, fast
                'transitionDuration': 1.5
            }
        
        # Prepare image URLs (copy to public directory)
        public_dir = os.path.join(self.remotion_dir, 'public', 'images', job_id or 'temp')
        os.makedirs(public_dir, exist_ok=True)
        
        image_urls = []
        for i, img_path in enumerate(image_paths):
            try:
                # Copy image to public directory
                filename = f"image_{i:03d}.jpg"
                dest_path = os.path.join(public_dir, filename)
                shutil.copy2(img_path, dest_path)
                
                # Create relative URL for Remotion
                image_urls.append(f"/images/{job_id or 'temp'}/{filename}")
                logger.info(f"Copied image {i+1}/{len(image_paths)}")
            except Exception as e:
                logger.error(f"Error copying image {img_path}: {e}")
        
        if not image_urls:
            logger.error("No images were successfully prepared")
            return None
        
        # Prepare props for Remotion
        props = {
            'images': image_urls,
            'propertyDetails': {
                'address': property_details.get('address', 'Beautiful Property'),
                'city': property_details.get('city', 'Your City, State'),
                'details': property_details.get('details1', 'Call for viewing'),
                'status': property_details.get('details2', 'Just Listed'),
                'agentName': property_details.get('agent_name', 'Your Agent'),
                'agentEmail': property_details.get('agent_email', 'agent@realestate.com'),
                'agentPhone': property_details.get('agent_phone', '(555) 123-4567'),
                'brandName': property_details.get('brand_name', 'Premium Real Estate')
            },
            'settings': settings
        }
        
        # Output filename
        output_filename = f"tour_{job_id or 'output'}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Build Remotion render command
        cmd = [
            'npx',
            'remotion',
            'render',
            'RealEstateTour',
            output_path,
            f'--props={json.dumps(props)}',
            '--log=verbose'
        ]
        
        logger.info(f"Starting Remotion render for {len(image_urls)} images...")
        logger.info(f"Settings: duration={settings['durationPerImage']}s, speed={settings['effectSpeed']}")
        
        try:
            # Change to Remotion directory
            original_dir = os.getcwd()
            os.chdir(self.remotion_dir)
            
            # Run Remotion render
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                shell=True  # Required for Windows
            )
            
            # Change back to original directory
            os.chdir(original_dir)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Video generated successfully: {output_path}")
                return output_path
            else:
                logger.error(f"Remotion render failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error running Remotion: {e}")
            os.chdir(original_dir)  # Ensure we change back
            return None
        finally:
            # Clean up temporary images
            try:
                shutil.rmtree(public_dir)
            except:
                pass
    
    def get_available_effects(self) -> Dict[str, str]:
        """Get available Ken Burns effects"""
        return {
            'zoomIn': 'Slowly zoom into the image',
            'zoomOut': 'Slowly zoom out from the image',
            'panLeft': 'Pan from right to left',
            'panRight': 'Pan from left to right',
            'panUp': 'Pan from bottom to top',
            'panDown': 'Pan from top to bottom',
            'zoomInPanLeft': 'Zoom in while panning left',
            'zoomInPanRight': 'Zoom in while panning right',
            'zoomOutPanUp': 'Zoom out while panning up',
            'zoomOutPanDown': 'Zoom out while panning down'
        }
    
    def get_speed_settings(self) -> Dict[str, Dict[str, any]]:
        """Get available speed settings"""
        return {
            'slow': {
                'description': 'Very subtle, elegant movement',
                'durationPerImage': 12,
                'effectSpeed': 'slow',
                'transitionDuration': 2
            },
            'medium': {
                'description': 'Moderate, professional movement',
                'durationPerImage': 8,
                'effectSpeed': 'medium',
                'transitionDuration': 1.5
            },
            'fast': {
                'description': 'Dynamic, energetic movement',
                'durationPerImage': 5,
                'effectSpeed': 'fast',
                'transitionDuration': 1
            }
        }


# Integration with existing app
def create_remotion_video(image_paths: List[str], 
                         property_details: Dict[str, str],
                         quality_preference: str = 'medium',
                         job_id: str = None) -> Optional[str]:
    """
    Create a video using Remotion instead of Creatomate
    
    Args:
        image_paths: List of image file paths
        property_details: Property information
        quality_preference: 'slow', 'medium', or 'fast'
        job_id: Unique job identifier
        
    Returns:
        Path to generated video or None
    """
    
    generator = RemotionVideoGenerator()
    
    # Map quality preference to settings
    speed_settings = generator.get_speed_settings()
    settings = speed_settings.get(quality_preference, speed_settings['medium'])
    
    # Remove description from settings
    settings = {k: v for k, v in settings.items() if k != 'description'}
    
    return generator.generate_video(
        image_paths=image_paths,
        property_details=property_details,
        settings=settings,
        job_id=job_id
    )


if __name__ == "__main__":
    # Test the integration
    print("Remotion Video Generator Test")
    print("="*50)
    
    # Example usage
    test_images = [
        "path/to/image1.jpg",
        "path/to/image2.jpg",
        "path/to/image3.jpg"
    ]
    
    test_details = {
        'address': '123 Beautiful Street',
        'city': 'Los Angeles, CA 90210',
        'details1': 'Call (555) 123-4567 for viewing',
        'details2': 'Just Listed',
        'agent_name': 'Jane Smith',
        'agent_email': 'jane@realestate.com',
        'agent_phone': '(555) 123-4567',
        'brand_name': 'Premium Real Estate'
    }
    
    print("\nTo use Remotion instead of Creatomate:")
    print("1. Set USE_CREATOMATE=false in environment")
    print("2. Set USE_REMOTION=true")
    print("3. Videos will be generated with custom Ken Burns effects")
    print("\nAvailable speed settings:")
    
    generator = RemotionVideoGenerator()
    for name, settings in generator.get_speed_settings().items():
        print(f"  {name}: {settings['description']}")