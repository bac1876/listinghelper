# Railway Setup Instructions for Creatomate Integration

## Fix Deployment Crash

The deployment should now work after the fixes. The crash was caused by:
1. Missing `requests` dependency in requirements.txt (now fixed)
2. Missing error handling for imports (now fixed)

## Environment Variables to Add in Railway

Go to your Railway project settings and add these environment variables:

### Required for Creatomate:
```
USE_CREATOMATE=true
CREATOMATE_API_KEY=561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3
CREATOMATE_TEMPLATE_ID=5c2eca01-84b8-4302-bad2-9189db4dae70
```

### Required for Cloudinary (for image hosting):
```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**IMPORTANT: You MUST add these Cloudinary credentials for the system to work with actual uploaded images!**

To get your Cloudinary credentials:
1. Sign up for a free account at https://cloudinary.com
2. Go to your Dashboard at https://cloudinary.com/console
3. Find your Cloud Name, API Key, and API Secret
4. Copy these values to Railway environment variables

### Optional (if you want to force premium quality for old system):
```
FORCE_PREMIUM_QUALITY=false
```

## How to Add Environment Variables in Railway:

1. Go to your Railway dashboard
2. Click on your project
3. Go to "Variables" tab
4. Click "New Variable"
5. Add each variable name and value
6. Railway will automatically redeploy

## Testing After Deployment:

1. Wait for deployment to complete (should take 2-3 minutes)
2. Go to https://virtual-tour-generator-production.up.railway.app/
3. Upload some property photos
4. Fill in property details (optional)
5. Click "Generate Virtual Tour"
6. You should get a professional video from Creatomate

## What's Working Now:

- Professional video generation using Creatomate API
- Smooth transitions and Ken Burns effects
- Property details and agent branding
- No more choppy videos or codec issues

## How It Works Now:

- System fully integrated with Cloudinary for image hosting
- Uploaded images are sent to Cloudinary first
- Cloudinary URLs are then passed to Creatomate
- Professional videos are generated with actual property photos
- No more example images - uses your real uploaded images!

## If Deployment Still Fails:

Check the Railway logs for specific error messages. Common issues:
- Network connectivity to Creatomate API
- Missing environment variables
- Memory limits (though Creatomate should use less memory)

## Success Indicators:

- Health check endpoint works: https://virtual-tour-generator-production.up.railway.app/api/virtual-tour/health
- No errors in Railway logs
- Videos generate successfully (using example images for now)