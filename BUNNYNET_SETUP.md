# Bunny.net Setup Guide for ListingHelper

## Why Switch to Bunny.net?

- **No video transformation limits** (ImageKit limits you to 500 seconds/month on free tier)
- **Much cheaper** - Pay-as-you-go pricing starting at $0.002/GB
- **14-day free trial** - No credit card required
- **Global CDN** with 119+ locations
- **Free video transcoding included**

## Quick Setup (5 minutes)

### Step 1: Create Bunny.net Account

1. Go to [bunny.net](https://bunny.net)
2. Click "Start Free Trial"
3. Sign up with your email (no credit card needed)

### Step 2: Create a Storage Zone

1. In the dashboard, go to **Storage** → **Storage Zones**
2. Click **"Add Storage Zone"**
3. Configure:
   - **Name**: `listinghelper` (or any name you prefer)
   - **Main Storage Region**: Choose closest to you (e.g., "New York" for US East)
   - **Pricing Tier**: Standard (default)
4. Click **"Add Storage Zone"**

### Step 3: Get Your API Credentials

1. Click on your new storage zone
2. Go to **"FTP & API Access"** tab
3. Copy these values:
   - **Storage Zone Name**: (e.g., `listinghelper`)
   - **Password**: This is your API key (click "Show Password" to reveal)
   - **Storage Hostname**: Note the region (e.g., `ny.storage.bunnycdn.com`)

### Step 4: Create a Pull Zone (CDN)

1. Go to **CDN** → **Pull Zones**
2. Click **"Add Pull Zone"**
3. Configure:
   - **Name**: `listinghelper-cdn` (or any name)
   - **Origin Type**: Select **"Storage Zone"**
   - **Storage Zone**: Select the storage zone you created
4. Click **"Add Pull Zone"**
5. Once created, copy the **CDN URL** (e.g., `https://listinghelper-cdn.b-cdn.net`)

### Step 5: Configure Environment Variables

Add these to your Railway environment variables:

```env
# Bunny.net Configuration
BUNNY_STORAGE_ZONE_NAME=listinghelper
BUNNY_ACCESS_KEY=your-storage-zone-password-here
BUNNY_PULL_ZONE_URL=https://listinghelper-cdn.b-cdn.net
BUNNY_REGION=  # Leave empty unless using non-default region

# Optional: Keep ImageKit as fallback
# (Keep your existing ImageKit variables if you want fallback)
```

### Step 6: Deploy to Railway

1. Commit and push the changes
2. Railway will automatically redeploy
3. Check logs to confirm "Using Bunny.net" message

## Testing the Integration

After deployment, your app will automatically use Bunny.net for:
- Uploading property images
- Storing generated videos
- Serving content through the CDN

## Cost Estimation

For typical usage:
- **Storage**: ~$0.01/GB/month
- **Bandwidth**: ~$0.01-0.03/GB
- **Total monthly cost**: Usually under $5-10 for moderate usage

Compare to ImageKit:
- **Free tier**: Only 500 seconds of video processing
- **Paid tier**: Starts at $89/month

## Troubleshooting

### "Storage backend not configured" error
- Verify all three Bunny.net environment variables are set in Railway
- Check that the storage zone password is correct

### Videos not uploading
- Ensure your Pull Zone is connected to your Storage Zone
- Verify the Pull Zone URL includes `https://`

### Slow uploads
- Choose a storage region closer to your Railway deployment
- Consider using multiple regions for global distribution

## Advanced Configuration

### Using Custom Domain
1. In Pull Zones, add a custom hostname
2. Update `BUNNY_PULL_ZONE_URL` to your custom domain

### Multi-Region Setup
1. Add replica regions in Storage Zone settings
2. Enable "Perma-Cache" in Pull Zone for better performance

## Support

- [Bunny.net Documentation](https://docs.bunny.net)
- [Bunny.net Support](https://support.bunny.net)
- Create an issue in this repo for integration-specific problems