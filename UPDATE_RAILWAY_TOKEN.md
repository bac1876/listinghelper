# URGENT: Update Railway GitHub Token

## The Problem
Your Railway deployment is currently failing with **"401 Bad credentials"** because the GitHub token has expired or been revoked.

## Quick Fix Steps

### 1. Generate New GitHub Token (MUST BE CLASSIC)

**IMPORTANT**: You need a "Classic" token, NOT a "Fine-grained" token!

1. Go to: https://github.com/settings/tokens?type=beta
2. Click **"Personal access tokens (classic)"** in the left sidebar
3. Click **"Generate new token"** → **"Generate new token (classic)"**
4. Name: `listinghelper-railway`
5. Expiration: **90 days** (or custom)
6. Select scopes:
   - ✅ **repo** (CHECK THE ENTIRE CHECKBOX - all sub-items)
   - ✅ **workflow** (separate checkbox below)
7. Scroll down and click **"Generate token"**
8. **COPY THE TOKEN IMMEDIATELY** (starts with `ghp_`)

### 2. Update Railway
1. Go to your Railway dashboard
2. Click on your service
3. Go to **Variables** tab
4. Find `GITHUB_TOKEN`
5. Click the edit icon
6. Paste your new token
7. Railway will auto-redeploy

### 3. Verify It Works
After Railway redeploys (takes ~2 minutes):
1. Upload some test images
2. The video should generate properly
3. Download should give you an MP4, not JSON

## What We Fixed in Code
- ✅ Fixed function signature mismatch that was causing fallback errors
- ✅ Added token validation with clear error messages
- ✅ Improved error handling to identify token issues immediately

## Current Token Status
Your current token (starting with `ghp_`) is **EXPIRED**

## Need Help?
If you still get JSON files after updating the token, check the Railway logs for any new error messages.