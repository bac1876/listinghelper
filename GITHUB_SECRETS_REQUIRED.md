# GitHub Repository Secrets Setup

## CRITICAL: Add These Secrets to GitHub Repository

The video generation is currently failing because the GitHub repository is missing required ImageKit secrets.

### How to Add Secrets to GitHub:

1. Go to: https://github.com/bac1876/listinghelper/settings/secrets/actions
2. Click "New repository secret" for each secret below
3. Add these exact secrets:

### Required Secrets:

#### ImageKit Secrets (MUST ADD - Videos Won't Upload Without These):
```
IMAGEKIT_PRIVATE_KEY = private_4NFY9DlW7DaZwHW1j+k5FsYoIhY=
IMAGEKIT_PUBLIC_KEY = public_wnhOBpqBUB1ReFbqsfOWgFcRnvU=
IMAGEKIT_URL_ENDPOINT = https://ik.imagekit.io/brianosris/
```

#### Optional Cloudinary Secrets (Already Present - Keep as Backup):
```
CLOUDINARY_CLOUD_NAME = dib3kbifc
CLOUDINARY_API_KEY = 245376524171559
CLOUDINARY_API_SECRET = vyExHjrHT59ssOXXB9c43vEuqTY
```

## Current Status:

Based on workflow analysis (Aug 8, 2025):
- **Run #104**: Video rendered successfully but failed to upload (missing ImageKit secrets)
- **Runs #106-108**: Failing immediately (35-41 seconds) due to missing secrets
- **Last successful video**: 7 hours ago when using Cloudinary

## Verification:

After adding the secrets, verify they're set correctly:
1. Go to https://github.com/bac1876/listinghelper/settings/secrets/actions
2. You should see all 3 ImageKit secrets listed (values will be hidden)
3. Run `py verify_github_secrets.py` to test the configuration

## Why This Is Happening:

1. The app was switched from Cloudinary to ImageKit to avoid the 100MB file size limit
2. The Railway deployment has the ImageKit secrets configured
3. But GitHub Actions (which renders the videos) doesn't have access to these secrets
4. Without the secrets, GitHub Actions can't upload the rendered videos to ImageKit

## Next Steps:

1. Add the ImageKit secrets to GitHub immediately
2. Test by creating a new virtual tour
3. Monitor the GitHub Actions workflow - it should take 2-5 minutes (not 35 seconds)
4. Check ImageKit media library for the new video

## Testing After Setup:

Run a test to ensure everything works:
```bash
py test_github_connection.py
```

This will verify:
- GitHub token is valid
- Can trigger workflows
- All required secrets are present