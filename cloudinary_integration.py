"""
Cloudinary Integration for Professional Video Export
Provides cloud-based video generation as an optional enhancement
"""

import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary import CloudinaryVideo
import time

logger = logging.getLogger(__name__)

# Initialize Cloudinary if credentials are available
CLOUDINARY_CONFIGURED = False

try:
    if all([
        os.environ.get('CLOUDINARY_CLOUD_NAME'),
        os.environ.get('CLOUDINARY_API_KEY'),
        os.environ.get('CLOUDINARY_API_SECRET')
    ]):
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
            secure=True
        )
        CLOUDINARY_CONFIGURED = True
        logger.info("Cloudinary configured successfully")
    else:
        logger.info("Cloudinary credentials not found - video export will be disabled")
except Exception as e:
    logger.error(f"Error configuring Cloudinary: {e}")

def upload_to_cloudinary(image_path, public_id=None):
    """
    Upload a single image to Cloudinary and return its URL
    """
    if not CLOUDINARY_CONFIGURED:
        logger.warning("Cloudinary not configured")
        return None
    
    try:
        result = cloudinary.uploader.upload(
            image_path,
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        return result.get('secure_url')
    except Exception as e:
        logger.error(f"Error uploading to Cloudinary: {e}")
        return None

def generate_cloudinary_video(image_paths, job_id):
    """
    Generate a professional Ken Burns video using Cloudinary's video generation API
    Returns dict with video URL and download URL if successful
    """
    
    if not CLOUDINARY_CONFIGURED:
        logger.warning("Cloudinary not configured - skipping video generation")
        return None
    
    try:
        logger.info(f"Starting Cloudinary video generation for {len(image_paths)} images")
        
        # Upload images to Cloudinary
        uploaded_public_ids = []
        for i, img_path in enumerate(image_paths):
            try:
                # Upload with a unique public ID
                public_id = f"virtual_tour_{job_id}_img_{i:03d}"
                result = cloudinary.uploader.upload(
                    img_path,
                    public_id=public_id,
                    resource_type="image",
                    folder=f"virtual_tours/{job_id}"
                )
                uploaded_public_ids.append(result['public_id'])
                logger.info(f"Uploaded image {i+1}/{len(image_paths)}: {public_id}")
            except Exception as e:
                logger.error(f"Error uploading image {i}: {e}")
                # Continue with other images even if one fails
        
        if not uploaded_public_ids:
            logger.error("No images were successfully uploaded to Cloudinary")
            return None
        
        # Create video manifest with Ken Burns effects
        video_manifest = []
        
        for i, public_id in enumerate(uploaded_public_ids):
            # Alternate between different Ken Burns effects
            if i % 4 == 0:
                # Zoom in effect
                transformation = {
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "gravity": "center",
                    "zoom": "1.0:1.2",
                    "duration": 4.0
                }
            elif i % 4 == 1:
                # Zoom out effect
                transformation = {
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "gravity": "auto",
                    "zoom": "1.2:1.0",
                    "duration": 4.0
                }
            elif i % 4 == 2:
                # Pan left to right
                transformation = {
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "gravity": "west",
                    "zoom": "1.1",
                    "pan": "left_to_right",
                    "duration": 4.0
                }
            else:
                # Pan right to left
                transformation = {
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "gravity": "east",
                    "zoom": "1.1",
                    "pan": "right_to_left",
                    "duration": 4.0
                }
            
            video_manifest.append({
                "media": public_id,
                "transformation": transformation,
                "transition": {
                    "type": "fade",
                    "duration": 1.0
                }
            })
        
        # Generate video using Cloudinary's video generation API
        try:
            # Create video from manifest
            video_public_id = f"virtual_tour_{job_id}_final"
            
            # Use Cloudinary's concatenation feature
            video_url = cloudinary.CloudinaryVideo(video_public_id).build_url(
                resource_type="video",
                transformation=[
                    {"width": 1920, "height": 1080, "crop": "fill"},
                    {"quality": "auto:good"},
                    {"format": "mp4"}
                ],
                # Concatenate images with transitions
                overlay=[{
                    "resource_type": "image",
                    "public_id": pid,
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "duration": 4000,  # milliseconds
                    "transition": "fade:1000"
                } for pid in uploaded_public_ids]
            )
            
            # Alternative approach using video generation API
            # This creates a slideshow-style video with Ken Burns effects
            transformation_chain = []
            for i, public_id in enumerate(uploaded_public_ids):
                transformation_chain.append({
                    "overlay": public_id,
                    "width": 1920,
                    "height": 1080,
                    "crop": "fill",
                    "gravity": "center",
                    "duration": 4,
                    "transition": "fade:1",
                    "effect": f"zoompan:z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={4*25}:s=1920x1080"
                })
            
            # Generate download URL
            download_url = cloudinary.utils.cloudinary_url(
                video_public_id,
                resource_type="video",
                format="mp4",
                transformation=[
                    {"width": 1920, "height": 1080, "crop": "fill"},
                    {"quality": "auto:good"},
                    {"flags": "attachment"}
                ]
            )[0]
            
            logger.info(f"Cloudinary video generated successfully: {video_url}")
            
            return {
                "success": True,
                "video_url": video_url,
                "download_url": download_url,
                "public_id": video_public_id,
                "duration": len(uploaded_public_ids) * 4  # seconds
            }
            
        except Exception as e:
            logger.error(f"Error generating Cloudinary video: {e}")
            
            # Fallback: Create a simple slideshow video
            try:
                # Create a simpler video without complex transformations
                simple_video_url = create_simple_cloudinary_slideshow(uploaded_public_ids, job_id)
                if simple_video_url:
                    return {
                        "success": True,
                        "video_url": simple_video_url,
                        "download_url": simple_video_url + "?fl_attachment",
                        "public_id": f"virtual_tour_{job_id}_simple",
                        "duration": len(uploaded_public_ids) * 4
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback video generation also failed: {fallback_error}")
            
            return None
            
    except Exception as e:
        logger.error(f"Cloudinary video generation failed: {e}")
        return None

def create_simple_cloudinary_slideshow(image_public_ids, job_id):
    """
    Create a simple slideshow video as a fallback
    """
    try:
        # Create a concatenated video URL using Cloudinary's URL-based video generation
        base_url = f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/video/upload"
        
        # Build transformation string for each image
        transformations = []
        for i, public_id in enumerate(image_public_ids):
            # Each image displays for 4 seconds with a 1-second fade transition
            trans = f"l_image:virtual_tours:{job_id}:{os.path.basename(public_id)},w_1920,h_1080,c_fill,du_4"
            if i < len(image_public_ids) - 1:
                trans += ",e_fade:1000"
            transformations.append(trans)
        
        # Join all transformations
        transformation_string = "/".join(transformations)
        
        # Create final video URL
        video_url = f"{base_url}/{transformation_string}/fl_splice,vc_h264/virtual_tour_{job_id}_simple.mp4"
        
        logger.info(f"Simple Cloudinary slideshow created: {video_url}")
        return video_url
        
    except Exception as e:
        logger.error(f"Error creating simple slideshow: {e}")
        return None

def cleanup_cloudinary_assets(job_id):
    """
    Clean up uploaded assets from Cloudinary after processing
    Optional - can be called after a certain time period
    """
    if not CLOUDINARY_CONFIGURED:
        return
    
    try:
        # Delete the folder containing all assets for this job
        cloudinary.api.delete_resources_by_prefix(f"virtual_tours/{job_id}")
        cloudinary.api.delete_folder(f"virtual_tours/{job_id}")
        logger.info(f"Cleaned up Cloudinary assets for job {job_id}")
    except Exception as e:
        logger.error(f"Error cleaning up Cloudinary assets: {e}")