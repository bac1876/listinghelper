"""
Watermark Configuration Module
Manages watermark settings, storage, and validation for video generation
"""

import os
import json
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Watermark storage directory - handle both Railway and local environments
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Railway production environment
    WATERMARK_STORAGE_DIR = '/app/storage/watermarks'
else:
    # Local development environment  
    WATERMARK_STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage', 'watermarks')

# Create directory if it doesn't exist
try:
    os.makedirs(WATERMARK_STORAGE_DIR, exist_ok=True)
except Exception as e:
    logger.warning(f"Could not create watermark storage directory: {e}")
    # Fallback to temp directory
    WATERMARK_STORAGE_DIR = os.path.join(tempfile.gettempdir(), 'watermarks')
    os.makedirs(WATERMARK_STORAGE_DIR, exist_ok=True)

# Supported watermark formats
SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}

# Maximum watermark file size (5MB)
MAX_WATERMARK_SIZE = 5 * 1024 * 1024

class WatermarkPosition:
    """Watermark positioning constants"""
    TOP_LEFT = 'top-left'
    TOP_RIGHT = 'top-right'
    TOP_CENTER = 'top-center'
    CENTER = 'center'
    BOTTOM_LEFT = 'bottom-left'
    BOTTOM_RIGHT = 'bottom-right'
    BOTTOM_CENTER = 'bottom-center'
    
    ALL_POSITIONS = [
        TOP_LEFT, TOP_RIGHT, TOP_CENTER,
        CENTER, BOTTOM_LEFT, BOTTOM_RIGHT, BOTTOM_CENTER
    ]

class WatermarkConfig:
    """Watermark configuration class"""
    
    def __init__(self, 
                 watermark_id: str = None,
                 filepath: str = None,
                 position: str = WatermarkPosition.BOTTOM_RIGHT,
                 opacity: float = 0.7,
                 scale: float = 0.1,
                 margin_x: int = 20,
                 margin_y: int = 20,
                 duration: str = 'full'):
        """
        Initialize watermark configuration
        
        Args:
            watermark_id: Unique identifier for the watermark
            filepath: Path to the watermark image file
            position: Position of watermark (see WatermarkPosition)
            opacity: Transparency level (0.0 to 1.0)
            scale: Size relative to video (0.01 to 0.5)
            margin_x: Horizontal margin in pixels
            margin_y: Vertical margin in pixels
            duration: When to show watermark ('full', 'start', 'end', or custom)
        """
        self.watermark_id = watermark_id or str(uuid.uuid4())
        self.filepath = filepath
        self.position = position
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp between 0 and 1
        self.scale = max(0.01, min(0.5, scale))  # Clamp between 1% and 50%
        self.margin_x = max(0, margin_x)
        self.margin_y = max(0, margin_y)
        self.duration = duration
        self.created_at = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'watermark_id': self.watermark_id,
            'filepath': self.filepath,
            'position': self.position,
            'opacity': self.opacity,
            'scale': self.scale,
            'margin_x': self.margin_x,
            'margin_y': self.margin_y,
            'duration': self.duration,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WatermarkConfig':
        """Create from dictionary"""
        return cls(
            watermark_id=data.get('watermark_id'),
            filepath=data.get('filepath'),
            position=data.get('position', WatermarkPosition.BOTTOM_RIGHT),
            opacity=data.get('opacity', 0.7),
            scale=data.get('scale', 0.1),
            margin_x=data.get('margin_x', 20),
            margin_y=data.get('margin_y', 20),
            duration=data.get('duration', 'full')
        )
    
    def get_ffmpeg_overlay_filter(self, video_width: int = 1920, video_height: int = 1080) -> str:
        """
        Generate FFmpeg overlay filter string for this watermark configuration
        
        Args:
            video_width: Target video width
            video_height: Target video height
            
        Returns:
            FFmpeg filter string for overlay
        """
        if not self.filepath or not os.path.exists(self.filepath):
            logger.warning(f"Watermark file not found: {self.filepath}")
            return ""
        
        # Calculate watermark size based on scale
        watermark_width = int(video_width * self.scale)
        watermark_height = int(video_height * self.scale)
        
        # Calculate position coordinates
        x, y = self._calculate_position_coordinates(
            video_width, video_height, 
            watermark_width, watermark_height
        )
        
        # Build filter components
        filter_parts = []
        
        # Scale the watermark
        filter_parts.append(f"scale={watermark_width}:{watermark_height}")
        
        # Set transparency if needed
        if self.opacity < 1.0:
            alpha_value = self.opacity
            filter_parts.append(f"format=rgba,colorchannelmixer=aa={alpha_value}")
        
        # Combine scaling and alpha filters
        watermark_filter = ",".join(filter_parts)
        
        # Create the overlay filter
        overlay_filter = f"overlay={x}:{y}"
        
        # Add duration constraints if needed
        if self.duration != 'full':
            if self.duration == 'start':
                overlay_filter += ":enable='between(t,0,5)'"  # First 5 seconds
            elif self.duration == 'end':
                overlay_filter += ":enable='gte(t,t-5)'"  # Last 5 seconds
        
        return f"[1:v]{watermark_filter}[wm];[0:v][wm]{overlay_filter}"
    
    def _calculate_position_coordinates(self, video_width: int, video_height: int, 
                                       watermark_width: int, watermark_height: int) -> Tuple[int, int]:
        """Calculate x,y coordinates for watermark position"""
        
        if self.position == WatermarkPosition.TOP_LEFT:
            x = self.margin_x
            y = self.margin_y
        elif self.position == WatermarkPosition.TOP_RIGHT:
            x = video_width - watermark_width - self.margin_x
            y = self.margin_y
        elif self.position == WatermarkPosition.TOP_CENTER:
            x = (video_width - watermark_width) // 2
            y = self.margin_y
        elif self.position == WatermarkPosition.CENTER:
            x = (video_width - watermark_width) // 2
            y = (video_height - watermark_height) // 2
        elif self.position == WatermarkPosition.BOTTOM_LEFT:
            x = self.margin_x
            y = video_height - watermark_height - self.margin_y
        elif self.position == WatermarkPosition.BOTTOM_RIGHT:
            x = video_width - watermark_width - self.margin_x
            y = video_height - watermark_height - self.margin_y
        elif self.position == WatermarkPosition.BOTTOM_CENTER:
            x = (video_width - watermark_width) // 2
            y = video_height - watermark_height - self.margin_y
        else:
            # Default to bottom right
            x = video_width - watermark_width - self.margin_x
            y = video_height - watermark_height - self.margin_y
        
        return max(0, x), max(0, y)

class WatermarkManager:
    """Manages watermark storage and configuration"""
    
    def __init__(self):
        self.storage_dir = WATERMARK_STORAGE_DIR
        self.config_file = os.path.join(self.storage_dir, 'watermarks.json')
        self._watermarks: Dict[str, WatermarkConfig] = {}
        self._load_watermarks()
    
    def _load_watermarks(self):
        """Load watermark configurations from storage"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for wm_data in data.get('watermarks', []):
                        config = WatermarkConfig.from_dict(wm_data)
                        self._watermarks[config.watermark_id] = config
                logger.info(f"Loaded {len(self._watermarks)} watermarks from storage")
        except Exception as e:
            logger.error(f"Error loading watermarks: {e}")
    
    def _save_watermarks(self):
        """Save watermark configurations to storage"""
        try:
            data = {
                'watermarks': [wm.to_dict() for wm in self._watermarks.values()],
                'updated_at': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._watermarks)} watermarks to storage")
        except Exception as e:
            logger.error(f"Error saving watermarks: {e}")
    
    def upload_watermark(self, file_data, filename: str, 
                        position: str = WatermarkPosition.BOTTOM_RIGHT,
                        opacity: float = 0.7, scale: float = 0.1,
                        margin_x: int = 20, margin_y: int = 20,
                        duration: str = 'full') -> WatermarkConfig:
        """
        Upload and store a new watermark
        
        Args:
            file_data: File data (from request.files)
            filename: Original filename
            position: Watermark position
            opacity: Transparency (0.0 to 1.0)
            scale: Size relative to video (0.01 to 0.5)
            margin_x: Horizontal margin
            margin_y: Vertical margin
            duration: When to show watermark
            
        Returns:
            WatermarkConfig object
            
        Raises:
            ValueError: If file is invalid or too large
        """
        # Validate file
        self._validate_watermark_file(file_data, filename)
        
        # Generate unique ID and filepath
        watermark_id = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1].lower()
        stored_filename = f"{watermark_id}{file_extension}"
        filepath = os.path.join(self.storage_dir, stored_filename)
        
        # Save file
        file_data.save(filepath)
        logger.info(f"Watermark saved: {filepath}")
        
        # Optimize image if needed
        self._optimize_watermark_image(filepath)
        
        # Create configuration
        config = WatermarkConfig(
            watermark_id=watermark_id,
            filepath=filepath,
            position=position,
            opacity=opacity,
            scale=scale,
            margin_x=margin_x,
            margin_y=margin_y,
            duration=duration
        )
        
        # Store configuration
        self._watermarks[watermark_id] = config
        self._save_watermarks()
        
        return config
    
    def get_watermark(self, watermark_id: str) -> Optional[WatermarkConfig]:
        """Get watermark configuration by ID"""
        return self._watermarks.get(watermark_id)
    
    def list_watermarks(self) -> List[WatermarkConfig]:
        """Get list of all watermarks"""
        return list(self._watermarks.values())
    
    def delete_watermark(self, watermark_id: str) -> bool:
        """Delete a watermark"""
        if watermark_id not in self._watermarks:
            return False
        
        config = self._watermarks[watermark_id]
        
        # Delete file
        try:
            if config.filepath and os.path.exists(config.filepath):
                os.remove(config.filepath)
                logger.info(f"Deleted watermark file: {config.filepath}")
        except Exception as e:
            logger.error(f"Error deleting watermark file: {e}")
        
        # Remove from memory and storage
        del self._watermarks[watermark_id]
        self._save_watermarks()
        
        return True
    
    def update_watermark_config(self, watermark_id: str, **kwargs) -> Optional[WatermarkConfig]:
        """Update watermark configuration"""
        if watermark_id not in self._watermarks:
            return None
        
        config = self._watermarks[watermark_id]
        
        # Update allowed fields
        if 'position' in kwargs and kwargs['position'] in WatermarkPosition.ALL_POSITIONS:
            config.position = kwargs['position']
        if 'opacity' in kwargs:
            config.opacity = max(0.0, min(1.0, float(kwargs['opacity'])))
        if 'scale' in kwargs:
            config.scale = max(0.01, min(0.5, float(kwargs['scale'])))
        if 'margin_x' in kwargs:
            config.margin_x = max(0, int(kwargs['margin_x']))
        if 'margin_y' in kwargs:
            config.margin_y = max(0, int(kwargs['margin_y']))
        if 'duration' in kwargs:
            config.duration = kwargs['duration']
        
        self._save_watermarks()
        return config
    
    def _validate_watermark_file(self, file_data, filename: str):
        """Validate uploaded watermark file"""
        # Check file extension
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format. Supported: {', '.join(SUPPORTED_FORMATS)}")
        
        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        if file_size > MAX_WATERMARK_SIZE:
            raise ValueError(f"File too large. Maximum size: {MAX_WATERMARK_SIZE / 1024 / 1024:.1f}MB")
        
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Try to validate as image
        temp_file_path = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file_path = temp_file.name
            temp_file.close()  # Close the file handle immediately
            
            file_data.save(temp_file_path)
            file_data.seek(0)  # Reset for future use
            
            with Image.open(temp_file_path) as img:
                # Check image dimensions
                if img.width < 10 or img.height < 10:
                    raise ValueError("Image too small (minimum 10x10 pixels)")
                if img.width > 4000 or img.height > 4000:
                    raise ValueError("Image too large (maximum 4000x4000 pixels)")
                
                logger.info(f"Watermark validation passed: {img.width}x{img.height}, {img.mode}")
            
        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # Ignore cleanup errors
            if "Invalid image file" not in str(e):
                raise ValueError(f"Invalid image file: {str(e)}")
            else:
                raise
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass  # Ignore cleanup errors
    
    def _optimize_watermark_image(self, filepath: str):
        """Optimize watermark image for better performance"""
        try:
            with Image.open(filepath) as img:
                # Convert to RGBA for transparency support
                if img.mode not in ('RGBA', 'LA'):
                    if img.mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    elif img.mode in ('RGB', 'L'):
                        # Add alpha channel
                        img = img.convert('RGBA')
                
                # Optimize and save
                img.save(filepath, optimize=True, format='PNG')
                logger.info(f"Optimized watermark: {filepath}")
                
        except Exception as e:
            logger.warning(f"Could not optimize watermark {filepath}: {e}")
    
    def cleanup_old_watermarks(self, days_old: int = 30):
        """Clean up watermarks older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        to_delete = []
        for wm_id, config in self._watermarks.items():
            try:
                created_date = datetime.fromisoformat(config.created_at)
                if created_date < cutoff_date:
                    to_delete.append(wm_id)
            except Exception as e:
                logger.warning(f"Could not parse date for watermark {wm_id}: {e}")
        
        for wm_id in to_delete:
            self.delete_watermark(wm_id)
            logger.info(f"Cleaned up old watermark: {wm_id}")
        
        return len(to_delete)

# Global watermark manager instance
watermark_manager = WatermarkManager()