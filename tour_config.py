"""
Virtual Tour Configuration
Customize the style and feel of the virtual tours
"""

# Tour Styles
TOUR_STYLES = {
    "luxury": {
        "name": "Luxury Estate",
        "description": "Slow, elegant movements for high-end properties",
        "base_duration": 8.0,  # 8 seconds per image for premium experience
        "transition_duration": 1.5,  # Smooth, unhurried transitions
        "zoom_range": (1.0, 1.25),  # Subtle zoom for elegance
        "movement_speed": 0.5,  # Very slow movement for luxury feel
        "vignette_strength": 0.20,
        "color_enhancement": 1.12,
        "preferred_movements": ["slow_zoom_in", "elegant_pan", "reveal"]
    },
    "modern": {
        "name": "Modern Home",
        "description": "Dynamic movements for contemporary properties",
        "base_duration": 4.0,
        "transition_duration": 0.8,
        "zoom_range": (1.1, 1.4),
        "movement_speed": 1.2,
        "vignette_strength": 0.1,
        "color_enhancement": 1.15,
        "preferred_movements": ["dynamic_pan", "quick_zoom", "diagonal"]
    },
    "cozy": {
        "name": "Cozy Home",
        "description": "Intimate, warm movements for smaller properties",
        "base_duration": 4.5,
        "transition_duration": 1.0,
        "zoom_range": (1.15, 1.45),
        "movement_speed": 0.9,
        "vignette_strength": 0.3,
        "color_enhancement": 1.05,
        "preferred_movements": ["intimate_zoom", "gentle_pan", "detail_focus"]
    },
    "commercial": {
        "name": "Commercial Space",
        "description": "Wide, informative movements for commercial properties",
        "base_duration": 5.0,
        "transition_duration": 0.6,
        "zoom_range": (0.95, 1.2),
        "movement_speed": 0.8,
        "vignette_strength": 0.05,
        "color_enhancement": 1.0,
        "preferred_movements": ["wide_establish", "systematic_pan", "overview"]
    }
}

# Movement Patterns
MOVEMENT_PATTERNS = {
    # Luxury movements
    "slow_zoom_in": {
        "description": "Elegant slow zoom to draw viewer in",
        "start_pos": (0.5, 0.5),
        "end_pos": (0.5, 0.5),
        "start_zoom": 1.0,
        "end_zoom": 1.25,
        "easing": "ease_in_out",
        "duration_multiplier": 1.2
    },
    "elegant_pan": {
        "description": "Smooth horizontal pan across space",
        "start_pos": (0.35, 0.5),
        "end_pos": (0.65, 0.5),
        "start_zoom": 1.15,
        "end_zoom": 1.15,
        "easing": "ease_in_out",
        "duration_multiplier": 1.1
    },
    "reveal": {
        "description": "Pull back to reveal full space",
        "start_pos": (0.5, 0.5),
        "end_pos": (0.5, 0.5),
        "start_zoom": 1.35,
        "end_zoom": 1.0,
        "easing": "ease_out",
        "duration_multiplier": 1.15
    },
    
    # Modern movements
    "dynamic_pan": {
        "description": "Quick pan to show space flow",
        "start_pos": (0.25, 0.5),
        "end_pos": (0.75, 0.5),
        "start_zoom": 1.2,
        "end_zoom": 1.25,
        "easing": "ease_in_out",
        "duration_multiplier": 0.9
    },
    "quick_zoom": {
        "description": "Dynamic zoom to feature",
        "start_pos": (0.5, 0.5),
        "end_pos": (0.6, 0.4),
        "start_zoom": 1.1,
        "end_zoom": 1.4,
        "easing": "ease_in",
        "duration_multiplier": 0.85
    },
    "diagonal": {
        "description": "Diagonal movement for modern feel",
        "start_pos": (0.3, 0.3),
        "end_pos": (0.7, 0.7),
        "start_zoom": 1.15,
        "end_zoom": 1.3,
        "easing": "ease_in_out",
        "duration_multiplier": 0.95
    },
    
    # Cozy movements
    "intimate_zoom": {
        "description": "Close, warm zoom on details",
        "start_pos": (0.5, 0.5),
        "end_pos": (0.5, 0.5),
        "start_zoom": 1.2,
        "end_zoom": 1.45,
        "easing": "ease_in",
        "duration_multiplier": 1.0
    },
    "gentle_pan": {
        "description": "Soft pan across cozy spaces",
        "start_pos": (0.4, 0.5),
        "end_pos": (0.6, 0.5),
        "start_zoom": 1.25,
        "end_zoom": 1.25,
        "easing": "ease_in_out",
        "duration_multiplier": 1.05
    },
    "detail_focus": {
        "description": "Focus on homey details",
        "start_pos": (0.6, 0.6),
        "end_pos": (0.6, 0.6),
        "start_zoom": 1.15,
        "end_zoom": 1.4,
        "easing": "ease_in",
        "duration_multiplier": 0.95
    },
    
    # Commercial movements
    "wide_establish": {
        "description": "Wide shot to show full space",
        "start_pos": (0.5, 0.5),
        "end_pos": (0.5, 0.5),
        "start_zoom": 0.95,
        "end_zoom": 1.05,
        "easing": "ease_in_out",
        "duration_multiplier": 1.1
    },
    "systematic_pan": {
        "description": "Methodical pan to show layout",
        "start_pos": (0.2, 0.5),
        "end_pos": (0.8, 0.5),
        "start_zoom": 1.1,
        "end_zoom": 1.1,
        "easing": "linear",
        "duration_multiplier": 1.2
    },
    "overview": {
        "description": "High-level overview movement",
        "start_pos": (0.5, 0.4),
        "end_pos": (0.5, 0.6),
        "start_zoom": 1.0,
        "end_zoom": 1.2,
        "easing": "ease_in_out",
        "duration_multiplier": 1.0
    }
}

# Music suggestions for each style
MUSIC_SUGGESTIONS = {
    "luxury": ["classical", "ambient piano", "orchestral"],
    "modern": ["electronic ambient", "minimal house", "contemporary"],
    "cozy": ["acoustic guitar", "soft jazz", "indie folk"],
    "commercial": ["corporate", "upbeat instrumental", "motivational"]
}

# Default settings
DEFAULT_STYLE = "luxury"
DEFAULT_FPS = 30
DEFAULT_RESOLUTION = (1920, 1080)
DEFAULT_OUTPUT_QUALITY = "high"  # high, medium, low

# Quality presets
QUALITY_PRESETS = {
    "high": {
        "fps": 30,
        "resolution": (1920, 1080),
        "bitrate": "8M",
        "codec": "libx264",
        "preset": "slow",
        "crf": 18
    },
    "medium": {
        "fps": 24,
        "resolution": (1280, 720),
        "bitrate": "4M",
        "codec": "libx264",
        "preset": "medium",
        "crf": 23
    },
    "low": {
        "fps": 24,
        "resolution": (854, 480),
        "bitrate": "2M",
        "codec": "libx264",
        "preset": "fast",
        "crf": 28
    }
}