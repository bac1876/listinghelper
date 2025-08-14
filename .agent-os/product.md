# ListingHelper - Virtual Tour Generator

## Product Mission

Transform real estate photography into professional cinematic virtual tours through automated video generation with Ken Burns effects, enabling real estate professionals to create compelling property marketing materials without video editing expertise.

## Product Goals

### Primary Goals
- **Cinematic Virtual Tours**: Generate professional MP4 videos with Ken Burns effects (zoom, pan movements) from real estate photos
- **Real Estate Marketing**: Provide ready-to-use marketing materials for property listings
- **Automated Processing**: Transform static photos into dynamic presentations with minimal user input
- **Professional Quality**: Output broadcast-quality 1080p videos suitable for MLS listings and social media

### Secondary Goals  
- **AI Enhancement**: Generate property descriptions and voiceover scripts
- **Multi-platform Deployment**: Support both cloud (Railway/GitHub Actions) and local processing
- **Scalable Processing**: Handle batch processing of multiple property sets

## Tech Stack

### Backend Services
- **Framework**: Flask 3.0.0 (Python web framework)
- **Video Processing**: FFmpeg (professional video encoding and effects)
- **Image Processing**: Pillow 10.2.0, OpenCV 4.8.1.78
- **Server**: Gunicorn 21.2.0 for production deployment

### Cloud Infrastructure
- **Primary Deployment**: Railway (https://railway.app)
  - Auto-deployment from GitHub
  - Persistent storage at `/app/storage`
  - Nixpacks build system
- **Alternative Processing**: GitHub Actions workflows
  - Remotion-based video generation
  - Artifact-based result distribution

### Video Generation Technologies
1. **FFmpeg Ken Burns** (Primary)
   - Direct FFmpeg commands with zoompan filters
   - H.264 encoding with libx264
   - 1920x1080 @ 25fps output
   
2. **Remotion Integration** (Alternative)
   - React-based video composition
   - TypeScript components for effects
   - Node.js 18+ runtime

3. **Cloud Storage Integration**
   - ImageKit.io for image/video hosting
   - Cloudinary as fallback option

### Frontend
- **Interface**: Pure HTML5/CSS3/JavaScript
- **Upload**: Drag & drop file interface
- **Progress**: Real-time WebSocket-based status updates
- **Download**: Direct file download links

### Development Tools
- **Browser Automation**: Playwright 1.55.0 (testing)
- **Container**: Docker with Python 3.11-slim base
- **Package Management**: pip (Python), npm (Node.js)

## Architecture Overview

### Core Processing Flow
```
[Photo Upload] → [Image Optimization] → [Ken Burns Generation] → [Video Export] → [Cloud Storage] → [Download Link]
```

### Service Architecture
- **Main Application** (`main.py`): Flask app with CORS, request logging, health checks
- **Video Processing** (`working_ken_burns.py`): Core Ken Burns video generation logic
- **GitHub Integration** (`working_ken_burns_github.py`): Alternative cloud-based processing
- **Cloud Storage** (`imagekit_integration.py`, `cloudinary_integration.py`): Asset management
- **Frontend** (`static/index.html`): User interface with real-time progress

### Data Flow
1. **Image Upload**: Multi-file drag & drop interface
2. **Job Tracking**: In-memory job status with unique IDs
3. **Processing**: FFmpeg-based Ken Burns effect application
4. **Storage**: Railway persistent storage + cloud backup
5. **Delivery**: Direct download + cloud URLs

### Ken Burns Effects Implementation
- **Zoom Patterns**: 1.0x to 1.5x cinematic zoom ranges
- **Pan Directions**: Alternating left-to-right, right-to-left movements
- **Duration**: 4 seconds per image (configurable)
- **Transitions**: Smooth crossfades between scenes
- **Quality**: CRF 20-25 for high-quality output

## Key Features & Functionality

### 1. Professional Video Generation
- **Ken Burns Effects**: Cinematic zoom and pan movements on static images
- **HD Output**: 1920x1080 Full HD resolution
- **Universal Format**: MP4 with H.264 encoding for maximum compatibility
- **Professional Codec**: libx264 with optimized settings for web delivery

### 2. Real Estate Focused
- **Property Descriptions**: AI-generated listing descriptions
- **Voiceover Scripts**: Professional narration scripts for tours
- **Batch Processing**: Multiple property handling
- **Duration Control**: Configurable time per image (2-8 seconds)

### 3. Cloud-First Architecture
- **Railway Deployment**: Automatic deployment from GitHub commits
- **Persistent Storage**: File retention across deployments
- **Health Monitoring**: Comprehensive system health checks
- **Scalable Processing**: GitHub Actions for compute-intensive operations

### 4. Advanced Processing Options
- **Multiple Backends**: FFmpeg direct, Remotion-based, cloud processing
- **Quality Settings**: Configurable compression and resolution
- **Effect Customization**: Speed, zoom range, transition timing
- **Fallback Systems**: Multiple processing paths for reliability

### 5. Developer Experience
- **Comprehensive Logging**: Detailed processing logs and error tracking
- **Testing Suite**: Automated browser testing with Playwright
- **Local Development**: Docker containerization for consistent environments
- **Debugging Tools**: Extensive diagnostic and monitoring scripts

### 6. Production Features
- **Error Handling**: Graceful degradation and retry mechanisms  
- **Progress Tracking**: Real-time status updates for long-running jobs
- **Timeout Management**: Configurable processing timeouts
- **Resource Cleanup**: Automatic cleanup of temporary files
- **Security**: CORS configuration and secure file handling

## Development Patterns

### Code Organization
- **Blueprint Pattern**: Flask blueprints for modular routing (`virtual_tour_bp`)
- **Integration Pattern**: Separate modules for each cloud service
- **Factory Pattern**: Conditional service loading based on environment
- **Job Pattern**: UUID-based job tracking with status updates

### Error Handling Strategy
- **Graceful Degradation**: Fallback to alternative processing methods
- **Comprehensive Logging**: Detailed error messages and stack traces
- **User Communication**: Clear error messages in frontend
- **Recovery Mechanisms**: Automatic retry for transient failures

### Testing Approach
- **Manual Testing**: Real estate photo test sets in `/test_images/`
- **Browser Testing**: Playwright automation for UI testing
- **Integration Testing**: End-to-end processing validation
- **Production Testing**: Live deployment health checks

### Deployment Strategy
- **GitOps**: Automatic deployment on GitHub commits
- **Environment Configuration**: Railway environment variables
- **Container-based**: Docker for consistent runtime environment
- **Health Checks**: Monitoring endpoints for system status

### Configuration Management
- **Environment Variables**: Secrets management via Railway/GitHub
- **Feature Flags**: Conditional service activation
- **Service Discovery**: Dynamic backend selection
- **Resource Management**: Configurable limits and timeouts

## Current Implementation Status

### Phase 0: Completed Features
- [x] **Flask Web Application**: Complete web server with CORS and logging
- [x] **File Upload Interface**: Drag & drop photo upload with progress tracking
- [x] **FFmpeg Integration**: Ken Burns video generation with professional settings
- [x] **Railway Deployment**: Production deployment with persistent storage
- [x] **Cloud Storage**: ImageKit and Cloudinary integration for asset hosting
- [x] **GitHub Actions**: Alternative processing pipeline with Remotion
- [x] **Health Monitoring**: Comprehensive system health and status endpoints
- [x] **Error Handling**: Graceful error recovery and user feedback
- [x] **Docker Containerization**: Production-ready container configuration
- [x] **Progress Tracking**: Real-time job status and progress updates

### Phase 1: Active Development
- [ ] **Performance Optimization**: Reduce processing time for large image sets
- [ ] **AI Integration**: Enhanced property description generation
- [ ] **Template System**: Multiple Ken Burns effect patterns
- [ ] **Quality Settings**: User-configurable output quality options

### Development Challenges Addressed
- **FFmpeg Complexity**: Simplified command generation with error handling
- **Processing Timeouts**: Implemented configurable timeout management
- **Cloud Integration**: Multiple fallback services for reliability
- **Memory Management**: Optimized processing for large image sets
- **Error Visibility**: Enhanced logging and debugging capabilities

## Technical Specifications

### Video Output Standards
- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 25 fps (cinematic standard)
- **Codec**: H.264 (libx264) with CRF 20-25
- **Container**: MP4 with faststart flag for web streaming
- **Duration**: 4 seconds per image (configurable)

### Ken Burns Effect Parameters
- **Zoom Range**: 1.0x to 1.5x (subtle, professional)
- **Pan Speed**: Coordinated with zoom timing
- **Direction Pattern**: Alternating for visual variety
- **Transition**: Smooth crossfade between images

### Infrastructure Requirements
- **Python**: 3.11+ (async support, modern features)
- **FFmpeg**: Full installation with libx264 codec
- **Memory**: 2GB+ recommended for HD processing
- **Storage**: Persistent storage for temporary files and outputs
- **Network**: High-bandwidth for cloud asset delivery

This product represents a comprehensive solution for real estate professionals requiring professional video marketing materials, combining ease of use with professional-grade output quality.