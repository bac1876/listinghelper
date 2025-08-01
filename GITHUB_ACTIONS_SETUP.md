# GitHub Actions Setup for Remotion Video Rendering

## Overview
This guide will help you set up GitHub Actions to render your real estate videos using Remotion, providing 2,000 free minutes per month.

## Step 1: GitHub Repository Setup

1. Push this code to your GitHub repository if you haven't already
2. Ensure the `.github/workflows/render-video.yml` file is in your repository

## Step 2: Add GitHub Secrets for Cloudinary

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these three secrets:

1. **CLOUDINARY_CLOUD_NAME**
   - Your Cloudinary cloud name (e.g., "your-cloud-name")
   
2. **CLOUDINARY_API_KEY**
   - Your Cloudinary API key (found in Dashboard)
   
3. **CLOUDINARY_API_SECRET**
   - Your Cloudinary API secret (found in Dashboard)

## Step 3: Create GitHub Personal Access Token

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "Railway Video Render"
4. Select these permissions:
   - `repo` (full control)
   - `workflow` (update GitHub Action workflows)
5. Generate token and COPY IT (you won't see it again!)

## Step 4: Update Railway Environment Variables

Add these environment variables to your Railway app:

```bash
# Enable GitHub Actions
USE_GITHUB_ACTIONS=true

# GitHub configuration
GITHUB_TOKEN=your_personal_access_token_here
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name

# Keep existing Cloudinary vars for fallback
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Step 5: Deploy and Test

1. Railway will automatically redeploy with the new environment variables
2. The app will now use GitHub Actions for high-quality Remotion rendering
3. Local FFmpeg rendering remains as a fallback

## How It Works

1. User uploads images to your Railway app
2. Railway triggers GitHub Actions workflow
3. GitHub Actions:
   - Spins up Ubuntu environment
   - Installs Remotion
   - Renders video with Ken Burns effects
   - Uploads to Cloudinary
   - Returns video URL
4. Railway app polls for completion and serves the video

## Usage Limits

- **Free tier**: 2,000 minutes/month
- **Additional minutes**: $0.008/minute
- **Video rendering time**: ~2-5 minutes per video

## Monitoring

Check your GitHub Actions usage:
- Go to Settings → Billing & plans → Usage this month

## Troubleshooting

### Workflow not triggering
- Check GITHUB_TOKEN has correct permissions
- Verify GITHUB_OWNER and GITHUB_REPO are correct
- Check Actions are enabled in repository settings

### Video not uploading to Cloudinary
- Verify Cloudinary secrets in GitHub
- Check Cloudinary upload preset allows unsigned uploads

### Timeout issues
- Default timeout is 30 minutes
- Adjust in workflow file if needed

## API Endpoints

### Trigger new video
```bash
POST /api/virtual-tour/upload
{
  "images": ["url1", "url2", ...],
  "property_details": {
    "address": "123 Main St",
    "city": "Your City, State",
    ...
  },
  "settings": {
    "durationPerImage": 8,
    "effectSpeed": "medium",
    "transitionDuration": 1.5
  }
}
```

### Check GitHub job status
```bash
GET /api/virtual-tour/check-github-job/{job_id}
```

## Next Steps

1. Test with sample images
2. Monitor GitHub Actions tab for job progress
3. Check Cloudinary for uploaded videos
4. Adjust settings as needed