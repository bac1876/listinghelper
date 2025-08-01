# Super Detailed Setup Guide - GitHub Actions for Video Rendering

This guide assumes you have never done this before. Follow each step exactly.

---

## 📋 What You'll Need Before Starting

1. Your Cloudinary account login details
2. Your GitHub account login details  
3. Your Railway account login details
4. About 10-15 minutes

---

## 🔍 Part 1: Finding Your Cloudinary Credentials

### Step 1: Log into Cloudinary
1. Open your web browser (Chrome, Edge, Firefox, etc.)
2. Go to: https://cloudinary.com
3. Click the "Sign In" button (usually top right)
4. Enter your email and password
5. Click "Log in"

### Step 2: Find Your Dashboard
1. After logging in, you should see your "Dashboard"
2. If not, click "Dashboard" in the menu

### Step 3: Copy Your Credentials
You'll see three important pieces of information. Keep this tab open, you'll need them soon:

1. **Cloud Name**: Something like `dxxxxxxxxx` or your custom name
2. **API Key**: A long number like `123456789012345`  
3. **API Secret**: A mix of letters/numbers like `abcDEF123-xyz789_ABC`

⚠️ **IMPORTANT**: Keep these secret! Don't share them with anyone.

---

## 🔐 Part 2: Adding Secrets to GitHub

### Step 1: Go to Your Repository Settings
1. Open a new browser tab
2. Go to exactly this URL: https://github.com/bac1876/listinghelper/settings/secrets/actions
3. If asked to sign in:
   - Enter your GitHub username: `bac1876`
   - Enter your GitHub password
   - Click "Sign in"

### Step 2: Add First Secret (Cloud Name)
1. You should see a page titled "Actions secrets and variables"
2. Click the green button that says **"New repository secret"**
3. You'll see two boxes:
   - **Name**: Type exactly: `CLOUDINARY_CLOUD_NAME` (must be in ALL CAPS)
   - **Secret**: Paste your Cloud Name from Cloudinary (from Part 1, Step 3)
4. Click the green **"Add secret"** button

### Step 3: Add Second Secret (API Key)
1. Click **"New repository secret"** again
2. Fill in:
   - **Name**: Type exactly: `CLOUDINARY_API_KEY` (must be in ALL CAPS)
   - **Secret**: Paste your API Key from Cloudinary
3. Click the green **"Add secret"** button

### Step 4: Add Third Secret (API Secret)
1. Click **"New repository secret"** one more time
2. Fill in:
   - **Name**: Type exactly: `CLOUDINARY_API_SECRET` (must be in ALL CAPS)
   - **Secret**: Paste your API Secret from Cloudinary
3. Click the green **"Add secret"** button

### ✅ Check Your Work
You should now see 3 secrets listed:
- CLOUDINARY_API_SECRET
- CLOUDINARY_API_KEY  
- CLOUDINARY_CLOUD_NAME

---

## 🔑 Part 3: Creating a GitHub Personal Access Token

### Step 1: Go to Token Settings
1. In the same browser (stay logged into GitHub)
2. Go to exactly this URL: https://github.com/settings/tokens/new
3. You might need to confirm your password again

### Step 2: Fill Out the Token Form
1. **Note** (this is like a name for your token): 
   - Type: `Railway Video Render - listinghelper`

2. **Expiration**: 
   - Click the dropdown
   - Select "90 days" (this is fine for now)

3. **Select scopes** (these are permissions):
   - Scroll down to find these checkboxes
   - ✅ Check the box next to **repo** (it will auto-check all sub-boxes)
   - ✅ Scroll down more and check the box next to **workflow**

### Step 3: Create the Token
1. Scroll to the very bottom
2. Click the green button **"Generate token"**

### Step 4: COPY YOUR TOKEN NOW!
1. You'll see a green box with your token (starts with `ghp_`)
2. Click the 📋 copy button next to it
3. **SAVE IT SOMEWHERE SAFE** like:
   - Open Notepad
   - Paste the token
   - Save the file as `github-token.txt` on your Desktop

⚠️ **SUPER IMPORTANT**: You will NEVER see this token again after leaving this page!

---

## 🚂 Part 4: Adding to Railway

### Step 1: Log into Railway
1. Open a new browser tab
2. Go to: https://railway.app
3. Click "Login" 
4. Sign in with your account

### Step 2: Find Your Project
1. Look for your `listinghelper` project
2. Click on it to open it

### Step 3: Go to Variables
1. Look for a "Variables" tab or "Environment Variables" section
2. Click on it

### Step 4: Add New Variables
You need to add 4 new variables. For each one:

1. Click **"New Variable"** or **"Add Variable"** button

2. **First Variable**:
   - Variable name: `USE_GITHUB_ACTIONS`
   - Value: `true`
   - Click Save/Add

3. **Second Variable**:
   - Variable name: `GITHUB_TOKEN`
   - Value: Paste your token that starts with `ghp_` (from Part 3)
   - Click Save/Add

4. **Third Variable**:
   - Variable name: `GITHUB_OWNER`
   - Value: `bac1876`
   - Click Save/Add

5. **Fourth Variable**:
   - Variable name: `GITHUB_REPO`  
   - Value: `listinghelper`
   - Click Save/Add

### Step 5: Wait for Redeploy
1. Railway will automatically redeploy your app
2. Look for a "Deploying..." or similar message
3. Wait about 1-2 minutes for it to finish

---

## ✅ Part 5: Verify Everything Works

### Option A: Check the Health Endpoint (Easiest)
1. Find your Railway app URL (something like `listinghelper-production.up.railway.app`)
2. Add `/api/virtual-tour/health` to the end
3. Visit that URL in your browser
4. You should see something that includes `"github_actions_available": true`

### Option B: Check GitHub Actions Page
1. Go to: https://github.com/bac1876/listinghelper/actions
2. You should see "Render Real Estate Video" workflow listed
3. If you see it, the connection is working!

---

## 🎉 You're Done!

Your app will now:
- Use GitHub Actions to render professional videos
- Get 2,000 free minutes per month
- Create videos with smooth Ken Burns effects

---

## ❓ Troubleshooting

### "I can't find my Cloudinary credentials"
- Log into Cloudinary.com
- Click on "Dashboard" 
- They're right there on the main page

### "I lost my GitHub token"
- No problem! Just create a new one
- Go to: https://github.com/settings/tokens
- Delete the old one if it's there
- Create a new one following Part 3 again

### "Railway isn't redeploying"
- Click on your service in Railway
- Look for a "Redeploy" button
- Click it manually

### "How do I know it's working?"
- When someone uploads images to your app
- Check https://github.com/bac1876/listinghelper/actions
- You'll see a new workflow running!

---

## 📞 Still Stuck?

If something isn't working:
1. Double-check every variable name is EXACTLY as shown (including CAPITAL LETTERS)
2. Make sure you copied the full token (starts with `ghp_`)
3. Verify all 3 Cloudinary secrets are in GitHub
4. Check that all 4 Railway variables are added

Remember: It's okay to delete everything and start over if needed!