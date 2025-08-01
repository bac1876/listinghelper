# URGENT: Railway Environment Variable Update Required

## The Issue
You're seeing the old template with stock photos because Railway still has the OLD template ID in environment variables.

## Required Update in Railway

Go to your Railway project's Variables tab and UPDATE this variable:

**OLD (incorrect):**
```
CREATOMATE_TEMPLATE_ID=5c2eca01-84b8-4302-bad2-9189db4dae70
```

**NEW (correct):**
```
CREATOMATE_TEMPLATE_ID=31b06afe-9073-4f68-a329-0e910a8be6a7
```

## Full Environment Variables Should Be:
```
USE_CREATOMATE=true
CREATOMATE_API_KEY=561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3
CREATOMATE_TEMPLATE_ID=31b06afe-9073-4f68-a329-0e910a8be6a7
CLOUDINARY_CLOUD_NAME=dib3kbifc
CLOUDINARY_API_KEY=245376524171559
CLOUDINARY_API_SECRET=vyExHjrHT59ssOXXB9c43vEuqTY
```

## After Updating:
1. Railway will automatically redeploy
2. Wait 2-3 minutes for deployment
3. Test with your images again
4. You should see the new template with YOUR images (not stock photos)

## Code Changes Made:
- Removed fallback stock images
- Added better logging
- Updated to use Video elements (not Photo)
- Maximum 4 images now (not 5)

The code is already pushed and ready - you just need to update the CREATOMATE_TEMPLATE_ID in Railway!