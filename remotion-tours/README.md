# Remotion Real Estate Tours

Custom Ken Burns video generator with full control over timing and movement speed.

## Features

- **Adjustable Speed**: Three speed settings (slow, medium, fast) for Ken Burns effects
- **Custom Timing**: Set duration per image (4-20 seconds)
- **Multiple Effects**: 
  - Zoom in/out
  - Pan left/right/up/down
  - Combined movements (zoom + pan)
- **Professional Overlays**: Property details with smooth animations
- **Smooth Transitions**: Customizable fade transitions between images

## Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start Remotion Studio** (visual editor):
   ```bash
   npm start
   ```

3. **Render a video**:
   ```bash
   npx remotion render RealEstateTour out/video.mp4
   ```

## Speed Settings

### Slow (Elegant, Subtle)
- 12 seconds per image
- Very gentle movements
- 2 second transitions
- Perfect for luxury properties

### Medium (Professional, Balanced)
- 8 seconds per image
- Moderate movements
- 1.5 second transitions
- Great for most properties

### Fast (Dynamic, Energetic)
- 5 seconds per image
- More dramatic movements
- 1 second transitions
- Good for social media

## Custom Props Example

```bash
npx remotion render RealEstateTour out/tour.mp4 --props='{
  "images": [
    "/path/to/image1.jpg",
    "/path/to/image2.jpg"
  ],
  "propertyDetails": {
    "address": "123 Beautiful Street",
    "city": "Los Angeles, CA 90210",
    "details": "Call for viewing",
    "status": "Just Listed",
    "agentName": "Jane Smith",
    "agentEmail": "jane@realestate.com",
    "agentPhone": "(555) 123-4567",
    "brandName": "Premium Real Estate"
  },
  "settings": {
    "durationPerImage": 10,
    "effectSpeed": "slow",
    "transitionDuration": 2
  }
}'
```

## Ken Burns Effects

The system automatically cycles through different effects:
1. **Zoom In**: Slowly zooms into the center
2. **Zoom Out**: Starts zoomed and pulls back
3. **Pan Left**: Moves from right to left
4. **Pan Right**: Moves from left to right
5. **Zoom + Pan**: Combines zoom with directional movement

## Integration with Main App

Use `remotion_integration.py` to integrate with your existing Flask app:

```python
from remotion_integration import create_remotion_video

video_path = create_remotion_video(
    image_paths=['image1.jpg', 'image2.jpg'],
    property_details={...},
    quality_preference='slow',  # or 'medium', 'fast'
    job_id='unique-id'
)
```

## Customization

Edit `src/KenBurnsImage.tsx` to:
- Add new movement patterns
- Adjust speed multipliers
- Create custom effects

Edit `src/PropertyDetails.tsx` to:
- Change overlay design
- Add animations
- Customize branding