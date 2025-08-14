# Technical Specification

This is the technical specification for the spec detailed in @.agent-os/specs/2025-08-14-watermark-feature/spec.md

## Technical Requirements

### Frontend Implementation
- **File Upload Component:** HTML5 file input with drag-and-drop support, restricted to PNG files with client-side validation for file type and size (max 5MB)
- **Position Selector:** Radio button group or visual grid selector for five positions (top-left, top-right, bottom-left, bottom-right, center)
- **Opacity Slider:** HTML range input (10-100%) with real-time value display and preview capability
- **Preview System:** Canvas-based watermark preview showing logo placement on sample background before video generation
- **Settings Storage:** LocalStorage-based persistence for watermark preferences during user session

### Backend FFmpeg Integration
- **File Processing:** Server-side PNG validation, automatic resizing for optimal video overlay (max 20% of video dimensions)
- **FFmpeg Overlay Filter:** Integration of `-vf overlay` filter into existing Ken Burns video generation pipeline
- **Position Calculations:** Automatic coordinate calculation for each position option with proper padding (5% from edges)
- **Opacity Handling:** Alpha channel manipulation through FFmpeg's `format=rgba,colorchannelmixer=aa=[opacity_value]` filter
- **Pipeline Enhancement:** Modification of existing `working_ken_burns.py` to include watermark overlay as final processing step

### Storage and Performance
- **Temporary Storage:** Store uploaded watermark files in `/app/storage/watermarks/` with unique session-based naming
- **Memory Optimization:** Watermark processing after Ken Burns effects to minimize memory usage during video generation
- **Error Handling:** Comprehensive validation for file format, size, and FFmpeg overlay command execution with fallback to non-watermarked video
- **Processing Time:** Estimated 2-5 second addition to existing video generation time per watermark application

### FFmpeg Command Structure
```bash
# Enhanced FFmpeg command with watermark overlay
ffmpeg -y \
  -f concat -safe 0 -i input_list.txt \
  -i watermark.png \
  -filter_complex "[0]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z=1.1:d=100:s=1920x1080:fps=25[bg];[1]format=rgba,colorchannelmixer=aa=0.7[logo];[bg][logo]overlay=W-w-W*0.05:H-h-H*0.05" \
  -c:v libx264 -preset fast -crf 25 -pix_fmt yuv420p \
  -movflags +faststart \
  output_with_watermark.mp4
```

## External Dependencies

No new external dependencies required. Implementation uses existing tech stack:
- **FFmpeg:** Already installed in Railway environment for overlay filter support
- **PIL (Pillow):** Already available for PNG file validation and basic image processing
- **Flask:** Current framework supports file upload handling
- **HTML5/JavaScript:** Native browser APIs for file handling and UI components