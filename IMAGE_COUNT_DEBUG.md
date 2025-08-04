# Image Count Debugging Guide

## Issue
You reported that only 2 images are being used in videos even though you upload 7.

## What We've Done

### 1. Added Detailed Logging
- **Railway App** (`working_ken_burns_github.py`):
  - Logs number of files received
  - Logs each file name and size
  - Logs files being uploaded to Cloudinary
  - Logs URLs after Cloudinary upload
  - Logs number of images sent to GitHub Actions

- **GitHub Actions** (`.github/workflows/render-video.yml`):
  - Logs raw images input
  - Logs parsed image count
  - Logs each individual image URL

### 2. Verified Components
- ✅ **Frontend**: Allows up to 15 images (`selectedFiles.slice(0, 15)`)
- ✅ **API**: No limits found in upload handling
- ✅ **Cloudinary Upload**: Uploads all files provided
- ✅ **Remotion**: Uses all images in the array

## How to Debug

### 1. Check Railway Logs
When you upload images, look for these log messages:
```
Received X files for job Y
  File 1: image1.jpg (12345 bytes)
  File 2: image2.jpg (23456 bytes)
  ...
Uploading X files to Cloudinary...
  Will upload file 1: image_0_photo1.jpg
  Will upload file 2: image_1_photo2.jpg
  ...
Successfully uploaded X images to Cloudinary
  Uploaded URL 1: https://...
  Uploaded URL 2: https://...
  ...
Triggering GitHub Actions with X images
```

### 2. Check GitHub Actions Logs
Go to: https://github.com/bac1876/listinghelper/actions

Find your workflow run and look for:
```
Raw images input:
["url1", "url2", "url3", ...]

Parsed image count:
Total images: X
  Image 1: https://...
  Image 2: https://...
  ...
```

### 3. Possible Causes

#### A. Frontend Issue
- File upload might be failing for some images
- Check browser console for errors

#### B. Server Processing
- Some files might be rejected (wrong format, too large)
- Check Railway logs for any skipped files

#### C. Cloudinary Upload
- Some uploads might fail
- Compare "Will upload" count vs "Successfully uploaded" count

#### D. GitHub Actions
- JSON parsing might truncate the array
- Check if "Raw images input" shows all URLs

## Test Process

1. **Test with known count**: Upload exactly 3, 5, or 7 images
2. **Note the job ID** from the UI
3. **Check Railway logs** for that job ID
4. **Check GitHub Actions** for the corresponding run
5. **Count images** at each step

## Quick Test Commands

Test with 3 images via API:
```bash
curl -X POST https://virtual-tour-generator-production.up.railway.app/api/virtual-tour/upload \
-H "Content-Type: application/json" \
-d '{"images":["url1","url2","url3"],"property_details":{...}}'
```

The logs will reveal where images are being lost in the pipeline.