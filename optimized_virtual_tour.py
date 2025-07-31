"""
Optimized Virtual Tour Generator for Memory-Constrained Environments
Uses streaming approach to minimize memory usage
"""

import os
import numpy as np
import logging
from PIL import Image, ImageFilter, ImageEnhance
import cv2
from dataclasses import dataclass
from typing import List, Tuple, Optional
import gc  # For garbage collection

logger = logging.getLogger(__name__)

# Quality presets - now with premium option for best results
OPTIMIZED_QUALITY_PRESETS = {
    "deployment": {
        "fps": 24,
        "resolution": (854, 480),  # 480p for low memory usage
        "bitrate": "1.5M",
        "codec": "libx264",
        "preset": "ultrafast",  # Fastest encoding
        "crf": 28
    },
    "medium": {
        "fps": 30,
        "resolution": (1280, 720),
        "bitrate": "4M",
        "codec": "libx264",
        "preset": "medium",
        "crf": 23
    },
    "high": {
        "fps": 30,
        "resolution": (1920, 1080),
        "bitrate": "8M",
        "codec": "libx264",
        "preset": "medium",
        "crf": 20
    },
    "premium": {
        "fps": 60,  # Smooth 60fps for professional quality
        "resolution": (1920, 1080),  # Full HD
        "bitrate": "12M",
        "codec": "libx264",
        "preset": "slow",  # Better quality encoding
        "crf": 18  # Higher quality (lower = better)
    }
}

@dataclass
class SimpleMovement:
    """Simplified movement pattern for memory efficiency"""
    zoom_start: float
    zoom_end: float
    pan_x: float
    pan_y: float
    duration: float

class OptimizedVirtualTour:
    def __init__(self, output_path: str, quality: str = 'deployment'):
        self.output_path = output_path
        self.quality = OPTIMIZED_QUALITY_PRESETS.get(quality, OPTIMIZED_QUALITY_PRESETS['deployment'])
        self.quality['name'] = quality  # Store quality name for duration calculation
        
        self.fps = self.quality['fps']
        self.width, self.height = self.quality['resolution']
        
        # Video writer setup with robust codec detection
        from video_codec_fix import get_working_video_writer
        
        self.writer, self.actual_output_path = get_working_video_writer(
            output_path, self.fps, self.width, self.height
        )
        
        if not self.writer:
            # Fallback to simple approach
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height), True)
            self.actual_output_path = output_path
            
            if not self.writer.isOpened():
                raise ValueError("Could not open video writer with any available codec")
            logger.warning("Using fallback mp4v codec")
    
    def get_simple_movement(self, index: int) -> SimpleMovement:
        """Get movement patterns with configurable duration based on quality"""
        # Longer durations for higher quality
        base_duration = {
            'deployment': 3.0,
            'medium': 4.5,
            'high': 6.0,
            'premium': 8.0  # 8 seconds per image for premium quality
        }.get(self.quality.get('name', 'high'), 5.0)
        
        movements = [
            SimpleMovement(1.0, 1.2, 0.05, 0.0, base_duration),    # Slower, smoother zoom in
            SimpleMovement(1.2, 1.0, -0.05, 0.0, base_duration),   # Gentle zoom out
            SimpleMovement(1.0, 1.15, 0.0, 0.05, base_duration),   # Subtle vertical movement
            SimpleMovement(1.15, 1.0, 0.0, -0.05, base_duration),  # Return movement
        ]
        return movements[index % len(movements)]
    
    def prepare_image_lightweight(self, image_path: str) -> np.ndarray:
        """Prepare image with minimal memory usage"""
        with Image.open(image_path) as img:
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Better color enhancement for premium quality
            quality_enhancement = {
                'deployment': 1.05,
                'medium': 1.08,
                'high': 1.10,
                'premium': 1.12
            }.get(self.quality.get('name', 'high'), 1.10)
            
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(quality_enhancement)
            
            # Add subtle sharpness for premium
            if self.quality.get('name') in ['high', 'premium']:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
            
            # Calculate scaling - use smaller buffer for movement
            img_aspect = img.width / img.height
            frame_aspect = self.width / self.height
            scale_factor = 1.3  # Less buffer = less memory
            
            if img_aspect > frame_aspect:
                new_height = int(self.height * scale_factor)
                new_width = int(new_height * img_aspect)
            else:
                new_width = int(self.width * scale_factor)
                new_height = int(new_width / img_aspect)
            
            # Resize with fast method
            img = img.resize((new_width, new_height), Image.Resampling.BILINEAR)
            
            # Convert to numpy and immediately close PIL image
            result = np.array(img)
            
        return result
    
    def write_frame_with_movement(self, image: np.ndarray, t: float, movement: SimpleMovement):
        """Extract and write a single frame with movement applied"""
        h, w = image.shape[:2]
        
        # Calculate current zoom and position
        zoom = movement.zoom_start + (movement.zoom_end - movement.zoom_start) * t
        
        # Calculate viewport
        viewport_w = self.width / zoom
        viewport_h = self.height / zoom
        
        # Calculate center with pan
        center_x = w / 2 + (movement.pan_x * w * t)
        center_y = h / 2 + (movement.pan_y * h * t)
        
        # Calculate crop boundaries
        x1 = max(0, int(center_x - viewport_w / 2))
        y1 = max(0, int(center_y - viewport_h / 2))
        x2 = min(w, int(x1 + viewport_w))
        y2 = min(h, int(y1 + viewport_h))
        
        # Extract and resize frame
        frame = image[y1:y2, x1:x2]
        frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Validate frame before writing
        if frame_bgr.shape[:2] != (self.height, self.width):
            logger.error(f"Frame size mismatch: expected {(self.height, self.width)}, got {frame_bgr.shape[:2]}")
            frame_bgr = cv2.resize(frame_bgr, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        
        # Ensure frame is uint8
        if frame_bgr.dtype != np.uint8:
            frame_bgr = frame_bgr.astype(np.uint8)
        
        # Write frame with error handling
        try:
            success = self.writer.write(frame_bgr)
            if not success:
                logger.error("Failed to write frame to video")
        except Exception as e:
            logger.error(f"Error writing frame: {e}")
    
    def add_simple_vignette(self, frame: np.ndarray) -> np.ndarray:
        """Add simple vignette effect with minimal computation"""
        h, w = frame.shape[:2]
        
        # Create simple radial gradient
        center_x, center_y = w // 2, h // 2
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Simple vignette calculation
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        vignette = 1 - (dist / max_dist) * 0.3
        vignette = np.clip(vignette, 0.7, 1.0)
        
        # Apply vignette
        for c in range(3):
            frame[:,:,c] = (frame[:,:,c] * vignette).astype(np.uint8)
        
        return frame
    
    def process_image_streaming(self, image_path: str, movement: SimpleMovement, apply_vignette: bool = False):
        """Process a single image and stream frames directly to video"""
        logger.info(f"Processing image: {os.path.basename(image_path)}")
        
        # Load and prepare image
        image = self.prepare_image_lightweight(image_path)
        
        # Calculate number of frames
        num_frames = int(movement.duration * self.fps)
        
        # Generate and write frames one at a time
        for i in range(num_frames):
            t = i / (num_frames - 1) if num_frames > 1 else 0
            t = self.ease_in_out(t)  # Simple easing
            
            # Write frame with movement
            self.write_frame_with_movement(image, t, movement)
        
        # Free memory
        del image
        gc.collect()
    
    def ease_in_out(self, t: float) -> float:
        """Smooth cubic ease in-out for professional movement"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            p = 2 * t - 2
            return 1 + p * p * p / 2
    
    def write_black_frames(self, count: int):
        """Write black frames"""
        black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for _ in range(count):
            try:
                self.writer.write(black_frame)
            except Exception as e:
                logger.error(f"Error writing black frame: {e}")
    
    def write_fade_in(self, image_path: str, duration: float = 0.5):
        """Write fade in from black"""
        image = self.prepare_image_lightweight(image_path)
        frame_rgb = self.extract_static_frame(image)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        num_frames = int(duration * self.fps)
        for i in range(num_frames):
            alpha = i / num_frames
            faded_frame = (frame_bgr * alpha).astype(np.uint8)
            try:
                self.writer.write(faded_frame)
            except Exception as e:
                logger.error(f"Error writing faded frame: {e}")
        
        del image, frame_rgb, frame_bgr
        gc.collect()
    
    def extract_static_frame(self, image: np.ndarray) -> np.ndarray:
        """Extract a static frame from image center"""
        h, w = image.shape[:2]
        
        # Calculate crop for frame aspect ratio
        img_aspect = w / h
        frame_aspect = self.width / self.height
        
        if img_aspect > frame_aspect:
            # Image is wider - crop width
            new_width = int(h * frame_aspect)
            x1 = (w - new_width) // 2
            cropped = image[:, x1:x1+new_width]
        else:
            # Image is taller - crop height
            new_height = int(w / frame_aspect)
            y1 = (h - new_height) // 2
            cropped = image[y1:y1+new_height, :]
        
        # Resize to output size
        return cv2.resize(cropped, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
    
    def write_simple_transition(self, image1_path: str, image2_path: str, duration: float = None):
        """Write a smooth crossfade transition between two images"""
        if duration is None:
            # Longer transitions for higher quality
            duration = {
                'deployment': 0.6,
                'medium': 0.8,
                'high': 1.0,
                'premium': 1.2
            }.get(self.quality.get('name', 'high'), 0.8)
        """Write a simple crossfade transition between two images"""
        # Load both images
        img1 = self.prepare_image_lightweight(image1_path)
        img2 = self.prepare_image_lightweight(image2_path)
        
        # Extract static frames
        frame1_rgb = self.extract_static_frame(img1)
        frame2_rgb = self.extract_static_frame(img2)
        
        # Convert to BGR
        frame1_bgr = cv2.cvtColor(frame1_rgb, cv2.COLOR_RGB2BGR)
        frame2_bgr = cv2.cvtColor(frame2_rgb, cv2.COLOR_RGB2BGR)
        
        # Write transition frames
        num_frames = int(duration * self.fps)
        for i in range(num_frames):
            alpha = i / (num_frames - 1)
            alpha = self.ease_in_out(alpha)
            
            # Crossfade
            frame = cv2.addWeighted(frame1_bgr, 1 - alpha, frame2_bgr, alpha, 0)
            try:
                self.writer.write(frame)
            except Exception as e:
                logger.error(f"Error writing transition frame: {e}")
        
        # Free memory
        del img1, img2, frame1_rgb, frame2_rgb, frame1_bgr, frame2_bgr
        gc.collect()
    
    def create_optimized_tour(self, image_paths: List[str]):
        """Create virtual tour with streaming approach"""
        logger.info(f"Creating optimized virtual tour with {len(image_paths)} images")
        
        # Add 0.5 second black at start
        self.write_black_frames(int(0.5 * self.fps))
        
        # Process each image
        for i, image_path in enumerate(image_paths):
            movement = self.get_simple_movement(i)
            
            if i == 0:
                # Fade in first image
                self.write_fade_in(image_path, duration=0.5)
            
            # Process image with movement
            self.process_image_streaming(image_path, movement)
            
            # Add transition to next image (except for last)
            if i < len(image_paths) - 1:
                self.write_simple_transition(image_path, image_paths[i + 1], duration=0.6)
        
        # Add fade out
        if image_paths:
            last_image = self.prepare_image_lightweight(image_paths[-1])
            frame_rgb = self.extract_static_frame(last_image)
            frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
            
            fade_frames = int(0.5 * self.fps)
            for j in range(fade_frames):
                alpha = 1 - (j / fade_frames)
                frame = (frame_bgr * alpha).astype(np.uint8)
                try:
                    self.writer.write(frame)
                except Exception as e:
                    logger.error(f"Error writing fade out frame: {e}")
            
            del last_image, frame_rgb, frame_bgr
            gc.collect()
        
        # Add 0.5 second black at end
        self.write_black_frames(int(0.5 * self.fps))
        
        # Clean up
        try:
            self.writer.release()
            cv2.destroyAllWindows()
        except Exception as e:
            logger.error(f"Error releasing video writer: {e}")
        
        # Verify output file (check actual output path which might be different)
        output_to_check = getattr(self, 'actual_output_path', self.output_path)
        if os.path.exists(output_to_check):
            file_size = os.path.getsize(output_to_check)
            if file_size > 0:
                logger.info(f"Optimized virtual tour created: {output_to_check} (size: {file_size / 1024 / 1024:.2f} MB)")
                # If output path changed (e.g., to AVI), rename to requested MP4
                if output_to_check != self.output_path and output_to_check.endswith('.avi'):
                    try:
                        os.rename(output_to_check, self.output_path)
                        logger.info(f"Renamed {output_to_check} to {self.output_path}")
                        return self.output_path
                    except:
                        logger.warning(f"Could not rename to MP4, returning {output_to_check}")
                        return output_to_check
                return output_to_check
            else:
                logger.error(f"Output file is empty: {output_to_check}")
                raise ValueError("Generated video file is empty")
        else:
            logger.error(f"Output file not found: {output_to_check}")
            raise ValueError("Failed to create video file")


def create_optimized_tour(image_paths: List[str], output_path: str, job_id: str, quality: str = None) -> str:
    """Main entry point for creating virtual tour with auto quality detection"""
    try:
        # Auto-detect quality based on environment
        if quality is None:
            if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_STATIC_URL'):
                quality = 'deployment'  # Use optimized for Railway
                logger.info("Detected Railway environment, using deployment quality")
            else:
                # Use premium quality when not on Railway
                quality = 'premium'
                logger.info("Using premium quality for best results (this may take 1-2 minutes)")
        
        logger.info(f"Creating virtual tour at {quality} quality for job {job_id}")
        
        # Log expected time
        expected_times = {
            'deployment': '10-20 seconds',
            'medium': '30-45 seconds',
            'high': '45-60 seconds',
            'premium': '60-120 seconds'
        }
        logger.info(f"Expected processing time: {expected_times.get(quality, '60 seconds')}")
        
        tour = OptimizedVirtualTour(output_path, quality=quality)
        return tour.create_optimized_tour(image_paths)
    except Exception as e:
        logger.error(f"Error creating optimized tour: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise