"""
Professional Virtual Tour Generator
Creates cinematic real estate tours with smooth camera movements
that simulate walking through a property
"""

import os
import numpy as np
import logging
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import math
import random
from tour_config import TOUR_STYLES, MOVEMENT_PATTERNS, QUALITY_PRESETS, DEFAULT_STYLE

logger = logging.getLogger(__name__)

@dataclass
class CameraMovement:
    """Defines a camera movement pattern"""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    start_zoom: float
    end_zoom: float
    duration: float
    easing: str = 'ease_in_out'

class ProfessionalVirtualTour:
    def __init__(self, output_path: str, style: str = DEFAULT_STYLE, quality: str = 'high'):
        self.output_path = output_path
        self.style = TOUR_STYLES.get(style, TOUR_STYLES[DEFAULT_STYLE])
        self.quality = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['high'])
        
        # Get settings from quality preset
        self.fps = self.quality['fps']
        self.width, self.height = self.quality['resolution']
        self.frame_count = 0
        
        # Get style-specific movement patterns
        self.movement_pool = [MOVEMENT_PATTERNS[m] for m in self.style['preferred_movements'] if m in MOVEMENT_PATTERNS]
        
        # Video writer setup with robust codec detection
        self.writer = None
        codecs_to_try = [
            ('H264', 'avc1'),  # H.264 - most compatible
            ('H264', 'h264'),
            ('H264', 'H264'),
            ('MPEG-4', 'mp4v'),
            ('MPEG-4', 'MP4V'),
            ('MJPEG', 'mjpeg')
        ]
        
        for codec_name, fourcc_code in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                self.writer = cv2.VideoWriter(
                    output_path, 
                    fourcc, 
                    self.fps, 
                    (self.width, self.height),
                    isColor=True
                )
                
                if self.writer.isOpened():
                    logger.info(f"Successfully opened video writer with codec: {codec_name} ({fourcc_code})")
                    break
                else:
                    logger.warning(f"Failed to open writer with codec: {codec_name} ({fourcc_code})")
                    self.writer.release()
                    self.writer = None
            except Exception as e:
                logger.warning(f"Error trying codec {codec_name}: {e}")
                if self.writer:
                    self.writer.release()
                self.writer = None
        
        if not self.writer or not self.writer.isOpened():
            raise ValueError("Could not open video writer with any available codec")
        
    def ease_in_out(self, t: float) -> float:
        """Smooth easing function for natural motion"""
        return t * t * (3.0 - 2.0 * t)
    
    def ease_in(self, t: float) -> float:
        """Accelerating from zero velocity"""
        return t * t
    
    def ease_out(self, t: float) -> float:
        """Decelerating to zero velocity"""
        return t * (2.0 - t)
    
    def apply_easing(self, t: float, easing: str) -> float:
        """Apply the specified easing function"""
        if easing == 'ease_in':
            return self.ease_in(t)
        elif easing == 'ease_out':
            return self.ease_out(t)
        else:
            return self.ease_in_out(t)
    
    def get_movement_pattern(self, index: int, image_aspect: float) -> CameraMovement:
        """Get a professional camera movement pattern based on style configuration"""
        # Select movement from style-specific pool
        movement_config = self.movement_pool[index % len(self.movement_pool)]
        
        # Apply style modifiers
        duration = self.style['base_duration'] * movement_config['duration_multiplier']
        duration *= self.style['movement_speed']
        
        # Adjust zoom range based on style
        zoom_min, zoom_max = self.style['zoom_range']
        start_zoom = movement_config['start_zoom']
        end_zoom = movement_config['end_zoom']
        
        # Scale zoom to style range
        zoom_range = end_zoom - start_zoom
        start_zoom = zoom_min + (start_zoom - 1.0) * (zoom_max - zoom_min)
        end_zoom = start_zoom + zoom_range * (zoom_max - zoom_min)
        
        return CameraMovement(
            start_x=movement_config['start_pos'][0],
            start_y=movement_config['start_pos'][1],
            end_x=movement_config['end_pos'][0],
            end_y=movement_config['end_pos'][1],
            start_zoom=start_zoom,
            end_zoom=end_zoom,
            duration=duration,
            easing=movement_config['easing']
        )
    
    def prepare_image(self, image_path: str) -> np.ndarray:
        """Prepare image with professional enhancements"""
        with Image.open(image_path) as img:
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Enhance image quality based on style
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.1)  # Slight contrast boost
            
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(self.style['color_enhancement'])  # Style-specific color enhancement
            
            # Add subtle brightness adjustment for consistency
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.02)
            
            # Calculate scaling to cover frame with room for movement
            img_aspect = img.width / img.height
            frame_aspect = self.width / self.height
            
            # Scale up by 1.5x to allow for zoom and pan
            scale_factor = 1.5
            
            if img_aspect > frame_aspect:
                # Image is wider
                new_height = int(self.height * scale_factor)
                new_width = int(new_height * img_aspect)
            else:
                # Image is taller
                new_width = int(self.width * scale_factor)
                new_height = int(new_width / img_aspect)
            
            # High-quality resize
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Apply subtle sharpening
            img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
            
            return np.array(img)
    
    def extract_frame(self, image: np.ndarray, x: float, y: float, zoom: float) -> np.ndarray:
        """Extract a frame from the image with given position and zoom"""
        h, w = image.shape[:2]
        
        # Calculate viewport size based on zoom
        viewport_w = self.width / zoom
        viewport_h = self.height / zoom
        
        # Calculate position in pixels
        center_x = x * w
        center_y = y * h
        
        # Calculate crop boundaries
        x1 = int(center_x - viewport_w / 2)
        y1 = int(center_y - viewport_h / 2)
        x2 = int(x1 + viewport_w)
        y2 = int(y1 + viewport_h)
        
        # Ensure boundaries are within image
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)
        
        # Extract and resize frame
        frame = image[y1:y2, x1:x2]
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
        
        return frame
    
    def create_transition(self, img1: np.ndarray, img2: np.ndarray, duration: Optional[float] = None) -> List[np.ndarray]:
        """Create smooth crossfade transition between images"""
        if duration is None:
            duration = self.style['transition_duration']
        
        frames = []
        num_frames = int(duration * self.fps)
        
        for i in range(num_frames):
            alpha = i / (num_frames - 1)
            alpha = self.ease_in_out(alpha)
            
            # Crossfade
            frame = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
            
            # Add subtle fade to black at midpoint
            if 0.4 < alpha < 0.6:
                darkness = 1 - abs(alpha - 0.5) * 4
                frame = (frame * (1 - darkness * 0.3)).astype(np.uint8)
            
            frames.append(frame)
        
        return frames
    
    def add_image_sequence(self, image_path: str, movement: CameraMovement, index: int):
        """Add an image with professional camera movement"""
        logger.info(f"Processing image {index}: {os.path.basename(image_path)}")
        
        # Prepare image
        image = self.prepare_image(image_path)
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        # Generate frames for this image
        num_frames = int(movement.duration * self.fps)
        frames = []
        
        for i in range(num_frames):
            t = i / (num_frames - 1)
            t_eased = self.apply_easing(t, movement.easing)
            
            # Interpolate position and zoom
            x = movement.start_x + (movement.end_x - movement.start_x) * t_eased
            y = movement.start_y + (movement.end_y - movement.start_y) * t_eased
            zoom = movement.start_zoom + (movement.end_zoom - movement.start_zoom) * t_eased
            
            # Extract frame
            frame = self.extract_frame(image_bgr, x, y, zoom)
            
            # Add vignette based on style
            vignette_strength = self.style['vignette_strength']
            if index == 0:  # Stronger vignette on first image
                frame = self.add_vignette(frame, strength=vignette_strength * 1.5)
            else:
                frame = self.add_vignette(frame, strength=vignette_strength)
            
            frames.append(frame)
        
        return frames
    
    def add_vignette(self, image: np.ndarray, strength: float = 0.2) -> np.ndarray:
        """Add subtle vignette effect"""
        h, w = image.shape[:2]
        
        # Create radial gradient
        Y, X = np.ogrid[:h, :w]
        center_y, center_x = h / 2, w / 2
        
        # Calculate distance from center
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Create vignette mask
        vignette = 1 - (dist_from_center / max_dist) * strength
        vignette = np.clip(vignette, 0, 1)
        vignette = vignette[..., np.newaxis]
        
        # Apply vignette
        return (image * vignette).astype(np.uint8)
    
    def create_tour(self, image_paths: List[str]):
        """Create the complete virtual tour"""
        all_frames = []
        
        # Add 1 second black at start
        black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for _ in range(self.fps):
            all_frames.append(black_frame)
        
        # Process each image
        for i, image_path in enumerate(image_paths):
            # Get movement pattern
            img_aspect = 1.5  # Approximate, will be calculated per image
            movement = self.get_movement_pattern(i, img_aspect)
            
            # Generate frames for this image
            frames = self.add_image_sequence(image_path, movement, i)
            
            # Add frames to video
            if i == 0:
                # First image - fade in from black
                fade_frames = int(0.5 * self.fps)
                for j in range(fade_frames):
                    alpha = j / fade_frames
                    frame = (frames[0] * alpha).astype(np.uint8)
                    all_frames.append(frame)
            
            # Add main frames
            all_frames.extend(frames)
            
            # Add transition to next image (except for last)
            if i < len(image_paths) - 1:
                next_movement = self.get_movement_pattern(i + 1, img_aspect)
                next_frames = self.add_image_sequence(image_paths[i + 1], next_movement, i + 1)
                
                # Create transition
                transition_frames = self.create_transition(frames[-1], next_frames[0])
                all_frames.extend(transition_frames[:-1])  # Avoid duplicate frame
        
        # Add fade out at end
        fade_frames = int(1.0 * self.fps)
        last_frame = all_frames[-1]
        for j in range(fade_frames):
            alpha = 1 - (j / fade_frames)
            frame = (last_frame * alpha).astype(np.uint8)
            all_frames.append(frame)
        
        # Add 0.5 second black at end
        for _ in range(int(0.5 * self.fps)):
            all_frames.append(black_frame)
        
        # Write all frames with validation
        logger.info(f"Writing {len(all_frames)} frames to video...")
        frames_written = 0
        for i, frame in enumerate(all_frames):
            # Validate frame
            if frame.shape[:2] != (self.height, self.width):
                logger.warning(f"Frame {i} size mismatch: expected {(self.height, self.width)}, got {frame.shape[:2]}")
                frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LANCZOS4)
            
            # Ensure frame is uint8
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)
            
            # Write frame with error handling
            try:
                success = self.writer.write(frame)
                if success:
                    frames_written += 1
                else:
                    logger.error(f"Failed to write frame {i}")
            except Exception as e:
                logger.error(f"Error writing frame {i}: {e}")
        
        logger.info(f"Successfully wrote {frames_written}/{len(all_frames)} frames")
        
        # Clean up
        try:
            self.writer.release()
            cv2.destroyAllWindows()
        except Exception as e:
            logger.error(f"Error releasing video writer: {e}")
        
        # Verify output file
        if os.path.exists(self.output_path):
            file_size = os.path.getsize(self.output_path)
            if file_size > 0:
                logger.info(f"Professional virtual tour created: {self.output_path} (size: {file_size / 1024 / 1024:.2f} MB)")
                return self.output_path
            else:
                logger.error(f"Output file is empty: {self.output_path}")
                raise ValueError("Generated video file is empty")
        else:
            logger.error(f"Output file not found: {self.output_path}")
            raise ValueError("Failed to create video file")


def create_professional_tour(image_paths: List[str], output_path: str, job_id: str, style: str = 'luxury', quality: str = 'high') -> str:
    """Main entry point for creating professional virtual tour"""
    try:
        # Check if running in memory-constrained environment
        import os
        if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('USE_OPTIMIZED_TOUR'):
            logger.info("Using optimized tour generator for deployment environment")
            from optimized_virtual_tour import create_optimized_tour
            return create_optimized_tour(image_paths, output_path, job_id, quality='deployment')
        
        logger.info(f"Creating {style} style tour at {quality} quality")
        logger.info(f"OpenCV version: {cv2.__version__}")
        
        tour = ProfessionalVirtualTour(output_path, style=style, quality=quality)
        return tour.create_tour(image_paths)
    except Exception as e:
        logger.error(f"Error creating professional tour: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise