# GitHub Token Setup for Remotion Video Rendering

## You Need to Create a GitHub Personal Access Token

### Step 1: Go to GitHub Token Settings
Click this link: https://github.com/settings/tokens/new

Or manually:
1. GitHub → Settings (your profile)
2. Developer settings (bottom of sidebar)
3. Personal access tokens → Tokens (classic)
4. Generate new token (classic)

### Step 2: Configure Your Token

**Note/Name:** `listinghelper-actions`

**Expiration:** Choose 90 days or longer

**Select Scopes (permissions):**
Check these boxes:
- ✅ **repo** (Full control of private repositories) - CHECK THIS ENTIRE SECTION
- ✅ **workflow** (Update GitHub Action workflows)

### Step 3: Generate and Copy Token

1. Click **"Generate token"** at the bottom
2. **COPY THE TOKEN IMMEDIATELY** (it looks like: `ghp_xxxxxxxxxxxxxxxxxxxx`)
3. You won't be able to see it again!

### Step 4: Add Token to Your .env File

Open `.env` and add:
```
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE
```

### Step 5: Add to Railway Environment Variables

1. Go to your Railway project
2. Variables tab
3. Add these 4 variables:
   - `USE_GITHUB_ACTIONS` = `true`
   - `GITHUB_TOKEN` = `ghp_YOUR_TOKEN_HERE`
   - `GITHUB_OWNER` = `bac1876`
   - `GITHUB_REPO` = `listinghelper`

## Test It Works

After adding the token, run:
```bash
py test_github_connection.py
```

This will verify:
- ✅ Token is valid
- ✅ Can access your repository
- ✅ Can trigger GitHub Actions
- ✅ Cloudinary secrets are in GitHub

## Summary

With this token, your app can:
1. Trigger GitHub Actions to render videos with Remotion
2. Check workflow status
3. Upload high-quality videos to Cloudinary

The token is like a password that lets your app talk to GitHub on your behalf.