# Final Setup Instructions

## Current Status:
- ✅ Both templates have Ken Burns movement effects
- ✅ New template (31b06afe) is configured in code
- ❌ Need to update Railway environment variable

## Required Action in Railway:

### Update this environment variable:
```
CREATOMATE_TEMPLATE_ID=31b06afe-9073-4f68-a329-0e910a8be6a7
```

### Full set of Railway environment variables:
```
USE_CREATOMATE=true
CREATOMATE_API_KEY=561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3
CREATOMATE_TEMPLATE_ID=31b06afe-9073-4f68-a329-0e910a8be6a7
CLOUDINARY_CLOUD_NAME=dib3kbifc
CLOUDINARY_API_KEY=245376524171559
CLOUDINARY_API_SECRET=vyExHjrHT59ssOXXB9c43vEuqTY
FLASK_ENV=production
PORT=5000
```

## About Timing:
- The new template should have better default timing than the original
- If it's still too fast, you have these options:
  1. Create a custom template in Creatomate with your preferred timing
  2. Ask Creatomate support for a template with 8-10 second per image timing
  3. Switch to local video generation (set USE_CREATOMATE=false)

## Next Steps:
1. Update the CREATOMATE_TEMPLATE_ID in Railway
2. Let Railway redeploy
3. Test with your images
4. If timing is still too fast, we can explore the other options

The new template uses 4 images instead of 5, which might also help with pacing.