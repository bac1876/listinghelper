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

# Memory-optimized quality presets
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
        "fps": 24,
        "resolution": (1280, 720),
        "bitrate": "3M",
        "codec": "libx264",
        "preset": "faster",
        "crf": 25
    },
    "high": {
        "fps": 30,
        "resolution": (1920, 1080),
        "bitrate": "5M",
        "codec": "libx264",
        "preset": "fast",
        "crf": 23
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
        
        self.fps = self.quality['fps']
        self.width, self.height = self.quality['resolution']
        
        # Video writer setup with optimized codec settings
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # More compatible codec
        self.writer = cv2.VideoWriter(
            output_path, 
            fourcc, 
            self.fps, 
            (self.width, self.height),
            isColor=True
        )
        
        if not self.writer.isOpened():
            # Fallback to another codec
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(output_path, fourcc, self.fps, (self.width, self.height))
    
    def get_simple_movement(self, index: int) -> SimpleMovement:
        """Get a simple movement pattern that looks professional but uses less computation"""
        movements = [
            SimpleMovement(1.0, 1.2, 0.1, 0.0, 3.0),    # Slow zoom in with slight pan right
            SimpleMovement(1.2, 1.0, -0.1, 0.0, 3.0),   # Zoom out with pan left
            SimpleMovement(1.0, 1.15, 0.0, 0.1, 3.0),   # Zoom in with pan down
            SimpleMovement(1.15, 1.0, 0.0, -0.1, 3.0),  # Zoom out with pan up
        ]
        return movements[index % len(movements)]
    
    def prepare_image_lightweight(self, image_path: str) -> np.ndarray:
        """Prepare image with minimal memory usage"""
        with Image.open(image_path) as img:
            # Convert to RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Light color enhancement only
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.05)
            
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
        
        # Write frame immediately
        self.writer.write(frame_bgr)
    
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
        """Simple ease in-out function"""
        return t * t * (3.0 - 2.0 * t)
    
    def write_black_frames(self, count: int):
        """Write black frames"""
        black_frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for _ in range(count):
            self.writer.write(black_frame)
    
    def write_fade_in(self, image_path: str, duration: float = 0.5):
        """Write fade in from black"""
        image = self.prepare_image_lightweight(image_path)
        frame_rgb = self.extract_static_frame(image)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        num_frames = int(duration * self.fps)
        for i in range(num_frames):
            alpha = i / num_frames
            faded_frame = (frame_bgr * alpha).astype(np.uint8)
            self.writer.write(faded_frame)
        
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
    
    def write_simple_transition(self, image1_path: str, image2_path: str, duration: float = 0.8):
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
            self.writer.write(frame)
        
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
                self.writer.write(frame)
            
            del last_image, frame_rgb, frame_bgr
            gc.collect()
        
        # Add 0.5 second black at end
        self.write_black_frames(int(0.5 * self.fps))
        
        # Clean up
        self.writer.release()
        cv2.destroyAllWindows()
        
        logger.info(f"Optimized virtual tour created: {self.output_path}")
        return self.output_path


def create_optimized_tour(image_paths: List[str], output_path: str, job_id: str, quality: str = 'deployment') -> str:
    """Main entry point for creating memory-optimized virtual tour"""
    try:
        logger.info(f"Creating optimized tour at {quality} quality for job {job_id}")
        tour = OptimizedVirtualTour(output_path, quality=quality)
        return tour.create_optimized_tour(image_paths)
    except Exception as e:
        logger.error(f"Error creating optimized tour: {e}")
        raise