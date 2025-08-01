# Step-by-Step Guide: Adding Environment Variables to Railway

## 1. Go to Your Railway Dashboard
- Open: https://railway.app/dashboard
- Find your project: **virtual-tour-generator**
- Click on it to open

## 2. Find the Variables Section
- Look at the top tabs in your project
- Click on **"Variables"** tab (usually between "Deployments" and "Settings")

## 3. Add Each Variable

### Method A: Raw Editor (Fastest)
1. Click **"RAW Editor"** button (if available)
2. Paste this entire block:
```
USE_CREATOMATE=true
CREATOMATE_API_KEY=561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3
CREATOMATE_TEMPLATE_ID=5c2eca01-84b8-4302-bad2-9189db4dae70
CLOUDINARY_CLOUD_NAME=dib3kbifc
CLOUDINARY_API_KEY=245376524171559
CLOUDINARY_API_SECRET=vyExHjrHT59ssOXXB9c43vEuqTY
```
3. Click **"Save"** or **"Update Variables"**

### Method B: One by One
1. Click **"New Variable"** button
2. Add first variable:
   - Variable name: `USE_CREATOMATE`
   - Value: `true`
   - Click "Add"
3. Repeat for each variable:

**Variable 2:**
- Name: `CREATOMATE_API_KEY`
- Value: `561802cc18514993874255b2dc4fcd1d0150ff961f26aab7d0aee02464704eac33aa94e133e90fa1bb8ac2742c165ab3`

**Variable 3:**
- Name: `CREATOMATE_TEMPLATE_ID`
- Value: `5c2eca01-84b8-4302-bad2-9189db4dae70`

**Variable 4:**
- Name: `CLOUDINARY_CLOUD_NAME`
- Value: `dib3kbifc`

**Variable 5:**
- Name: `CLOUDINARY_API_KEY`
- Value: `245376524171559`

**Variable 6:**
- Name: `CLOUDINARY_API_SECRET`
- Value: `vyExHjrHT59ssOXXB9c43vEuqTY`

## 4. Railway Will Auto-Deploy
- After adding variables, Railway automatically redeploys
- Look for a new deployment starting
- Wait 2-3 minutes for it to complete

## 5. Verify It's Working
- Check deployment logs for any errors
- Visit: https://virtual-tour-generator-production.up.railway.app/
- Try uploading some test images

## Common Issues:

**Can't find Variables tab?**
- Make sure you're in the project view, not the dashboard
- It might be under "Settings" → "Variables" on some versions

**Variables not saving?**
- Make sure there are no extra spaces
- Don't include quotes around values
- Click Save/Update after adding

**Need visual help?**
The Variables section usually looks like:
- A list of existing variables (if any)
- An "Add Variable" or "New Variable" button
- Sometimes a "RAW Editor" toggle

Let me know which step you're on and I can help further!