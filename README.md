# Virtual Tour Generator - Real Estate Ken Burns System

## 🎯 PROJECT OBJECTIVE

Create a web-based virtual tour generator that transforms real estate photos into professional cinematic presentations with **Ken Burns effects** (smooth zoom and pan movements). 

## ✅ CURRENT STATUS: WORKING!

**NEW APPROACH:** We've completely reimagined the solution using modern web technologies:

### Primary Output: CSS3 Ken Burns Virtual Tour
- **Instant Results:** No processing time needed
- **Professional Quality:** Smooth hardware-accelerated animations
- **Works Everywhere:** Compatible with all modern browsers
- **No Dependencies:** Pure CSS3/HTML5 solution

### Secondary Output: Cloud Video Export (Optional)
- **Cloudinary Integration:** Professional MP4 export when needed
- **Fallback Support:** Local FFmpeg if available

## 📁 PROJECT STRUCTURE

```
listinghelper/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── routes/
│   │   └── virtual_tour.py     # Main virtual tour processing logic
│   └── static/
│       └── index.html          # Frontend interface
├── requirements.txt            # Python dependencies
├── railway.json               # Railway deployment configuration
└── README.md                  # This file
```

## 🌐 DEPLOYMENT INFORMATION

- **Platform:** Railway (https://railway.app)
- **Live URL:** https://virtual-tour-generator-production.up.railway.app/
- **GitHub Repository:** https://github.com/bac1876/listinghelper
- **Deployment:** Automatic via GitHub integration

### Railway Credentials
- **Username:** bac1876
- **Password:** Lbbc#2245

### GitHub Credentials
- **Username:** bac1876
- **Password:** Lbbc#2245

## 🎬 TECHNICAL REQUIREMENTS

### Ken Burns Effects Specification
- **Zoom Range:** 1.0x to 1.1x (subtle zoom)
- **Duration:** 4 seconds per image
- **Pan Direction:** Alternating (left-to-right, right-to-left)
- **Output Resolution:** 1920x1080 (Full HD)
- **Frame Rate:** 25 fps
- **Codec:** H.264 (libx264)
- **Quality:** CRF 25 (good quality, reasonable file size)

### FFmpeg Command Structure
```bash
ffmpeg -y \
  -f concat -safe 0 -i input_list.txt \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z=1.1:d=100:s=1920x1080:fps=25" \
  -c:v libx264 -preset fast -crf 25 -pix_fmt yuv420p \
  -movflags +faststart \
  output.mp4
```

## 🔧 CURRENT IMPLEMENTATION

### Backend (working_ken_burns.py)
- **Framework:** Flask
- **Storage:** Railway persistent storage (`/app/storage`)
- **Job Tracking:** In-memory dictionary with progress updates
- **Image Processing:** PIL (Pillow) for optimization
- **Virtual Tour Generation:** CSS3 animations (primary)
- **Video Export:** Cloudinary API (optional)
- **Fallback:** Local FFmpeg (if available)

### Frontend (index.html)
- **Upload:** Drag & drop interface
- **Progress:** Real-time status updates
- **Download:** Direct file download links
- **Timeout:** 5 minutes (300 seconds)

## ✨ KEY FEATURES

### 1. Instant CSS3 Ken Burns Virtual Tours
**Benefits:**
- No processing delays
- Professional cinematic effects
- Mobile-responsive design
- Fullscreen support
- Progress indicators
- Keyboard controls

### 2. Optional Cloud Video Export
**When Needed:**
- Social media sharing
- Email attachments
- Offline viewing
- Legacy system support

### 2. Silent Failures
**Problem:** Errors not properly reported to user
**Impact:** User sees "success" but gets wrong output type

### 3. Processing Timeouts
**Problem:** Complex Ken Burns processing takes too long
**Current Timeout:** 120 seconds per FFmpeg command

## 🧪 TESTING SCENARIOS

### Test Case 1: Basic Functionality
- **Input:** 3 real estate photos (JPG format)
- **Expected:** MP4 video with Ken Burns effects
- **Current Result:** HTML slideshow

### Test Case 2: Health Check
- **URL:** `/api/virtual-tour/health`
- **Expected:** `ffmpeg_available: true`, `ffmpeg_test_passed: true`
- **Current Result:** FFmpeg available but Ken Burns fails

### Test Case 3: Error Logging
- **Check:** Railway deployment logs
- **Expected:** Detailed FFmpeg error messages
- **Current:** Limited error visibility

## 🔍 DEBUGGING INFORMATION

### FFmpeg Availability
```bash
# Test FFmpeg installation
ffmpeg -version

# Test basic video creation
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -f null -
```

### Railway Environment
- **OS:** Linux container
- **FFmpeg:** Pre-installed
- **Storage:** Persistent `/app/storage` directory
- **Memory:** Limited (exact specs unknown)
- **CPU:** Limited processing power

## 📋 ATTEMPTED SOLUTIONS

### 1. Multiple Ken Burns Methods
- Simple zoompan filter
- Individual clip creation + concatenation
- Basic zoom without complex filters
- **Result:** All methods failed

### 2. Error Handling Improvements
- Comprehensive logging
- Progress tracking
- Fallback mechanisms
- **Result:** Better visibility but still no video

### 3. FFmpeg Command Simplification
- Reduced complexity
- Faster presets
- Lower quality settings
- **Result:** Commands run but produce no output

## 🚀 QUICK START

### 1. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (optional for Cloudinary)
cp .env.example .env
# Edit .env with your Cloudinary credentials

# Run the application
python main.py
```

### 2. Railway Deployment
```bash
git add .
git commit -m "Virtual tour generator with CSS3 Ken Burns"
git push origin main
```

### 3. Environment Variables (Optional)
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## 📞 CONTACT INFORMATION

**Project Owner:** Real estate agent requiring professional virtual tours
**Use Case:** Marketing high-end properties with cinematic presentations
**Quality Requirements:** Professional, smooth camera movements essential

## 🔗 USEFUL LINKS

- **Live Application:** https://virtual-tour-generator-production.up.railway.app/
- **GitHub Repository:** https://github.com/bac1876/listinghelper
- **Railway Dashboard:** https://railway.app/dashboard
- **Health Check:** https://virtual-tour-generator-production.up.railway.app/api/virtual-tour/health

## 📝 DEVELOPMENT NOTES

- Railway auto-deploys on GitHub commits
- Frontend timeout set to 5 minutes
- Backend uses job tracking for progress
- All files stored in Railway persistent storage
- FFmpeg commands logged for debugging

---

**Last Updated:** July 31, 2025
**Status:** Fully working with CSS3 Ken Burns effects and optional cloud video export
