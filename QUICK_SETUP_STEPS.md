# Quick Setup Steps for GitHub Actions

Your GitHub repository is ready at: https://github.com/bac1876/listinghelper

## Step 1: Add Cloudinary Secrets to GitHub

1. **Go to your repository secrets page:**
   https://github.com/bac1876/listinghelper/settings/secrets/actions

2. **Add these three secrets** (click "New repository secret" for each):
   
   - **CLOUDINARY_CLOUD_NAME**
     - Value: Your Cloudinary cloud name
   
   - **CLOUDINARY_API_KEY**
     - Value: Your Cloudinary API key
   
   - **CLOUDINARY_API_SECRET**
     - Value: Your Cloudinary API secret

## Step 2: Create GitHub Personal Access Token

1. **Go to:** https://github.com/settings/tokens/new

2. **Fill in:**
   - Note: `Railway Video Render - listinghelper`
   - Expiration: 90 days (or your preference)
   - Scopes: Check these boxes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)

3. **Click "Generate token"**

4. **COPY THE TOKEN IMMEDIATELY!** (You won't see it again)

## Step 3: Add to Railway Environment Variables

Add these to your Railway app:

```
USE_GITHUB_ACTIONS=true
GITHUB_TOKEN=<paste_your_personal_access_token_here>
GITHUB_OWNER=bac1876
GITHUB_REPO=listinghelper
```

## Step 4: Test It!

Once Railway redeploys, test with:

```bash
curl -X POST https://your-railway-app.railway.app/api/virtual-tour/upload \
  -H "Content-Type: application/json" \
  -d '{
    "images": [
      "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&h=1080&fit=crop",
      "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1920&h=1080&fit=crop",
      "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1920&h=1080&fit=crop"
    ],
    "property_details": {
      "address": "123 Test Street",
      "city": "Test City, CA"
    }
  }'
```

## Monitor Progress

Watch your video render at: https://github.com/bac1876/listinghelper/actions

---

That's it! You'll have professional Ken Burns videos with 2,000 free minutes/month! 🎬