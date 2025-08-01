# Migration Guide: Creatomate → GitHub Actions + Remotion

## Overview
This guide helps you migrate from Creatomate to GitHub Actions with Remotion for video rendering.

## Why Migrate?
- **Full Control**: Remotion gives you complete programmatic control over Ken Burns effects
- **Free Tier**: 2,000 minutes/month free with GitHub Actions
- **Better Timing**: Precise control over speed, duration, and transitions
- **Cost Effective**: ~$0.008/minute after free tier vs Creatomate pricing

## Migration Steps

### 1. Set Up GitHub Repository
```bash
# Push your code to GitHub if not already done
git add .
git commit -m "Prepare for GitHub Actions migration"
git push origin main
```

### 2. Configure GitHub Secrets (Automated)
```bash
# Option 1: Python/Playwright (recommended)
python setup_github_secrets.py

# Option 2: PowerShell (Windows)
.\setup_github_secrets.ps1
```

### 3. Update Railway Environment Variables

**Remove these:**
- `CREATOMATE_API_KEY`
- `CREATOMATE_TEMPLATE_ID`
- `USE_CREATOMATE`

**Add these:**
```
USE_GITHUB_ACTIONS=true
GITHUB_TOKEN=your_personal_access_token
GITHUB_OWNER=your_github_username
GITHUB_REPO=your_repository_name
```

### 4. Clean Up Creatomate Files (Optional)
```bash
python remove_creatomate.py
```

### 5. Test the New System
```bash
# Test GitHub Actions integration
python test_github_actions.py

# Or test via API
curl -X POST https://your-app.railway.app/api/virtual-tour/upload \
  -H "Content-Type: application/json" \
  -d '{
    "images": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ],
    "property_details": {
      "address": "123 Main St",
      "city": "Your City, CA"
    },
    "settings": {
      "durationPerImage": 8,
      "effectSpeed": "medium",
      "transitionDuration": 1.5
    }
  }'
```

## What Changes for Users?

### API Endpoints
- **Same**: `/api/virtual-tour/upload` - Upload images and create tours
- **Same**: `/api/virtual-tour/download/{job_id}` - Download videos
- **Same**: `/api/virtual-tour/view/{job_id}` - View virtual tour
- **New**: `/api/virtual-tour/check-github-job/{job_id}` - Check GitHub job status

### Video Quality
- **Better**: Remotion produces higher quality videos
- **Customizable**: Full control over Ken Burns effects
- **Speed Options**: `slow`, `medium`, `fast`

### Processing Time
- **Creatomate**: 30-60 seconds
- **GitHub Actions**: 2-5 minutes (but free!)
- **Local FFmpeg**: Still available as instant fallback

## Rollback Plan

If you need to rollback to Creatomate:

1. Restore environment variables:
   ```
   USE_CREATOMATE=true
   CREATOMATE_API_KEY=your_key
   CREATOMATE_TEMPLATE_ID=your_template_id
   ```

2. Change import in `main.py`:
   ```python
   from working_ken_burns import virtual_tour_bp
   ```

3. Restore Creatomate files from `.backup` if removed

## Cost Comparison

### Creatomate
- Pay per render
- Limited control over effects
- Fast processing

### GitHub Actions + Remotion
- **Free**: 2,000 minutes/month
- **Overage**: $0.008/minute
- **Example**: 100 videos × 3 min = 300 minutes = FREE
- **Full control** over every aspect

## Monitoring

### GitHub Actions Usage
- Go to: Settings → Billing & plans → Usage this month
- Monitor: Actions minutes used

### Workflow Runs
- Go to: Actions tab in your repository
- See: All video render jobs

## Support

### Issues with GitHub Actions?
1. Check workflow logs in Actions tab
2. Verify GitHub secrets are set correctly
3. Ensure Personal Access Token has correct permissions

### Issues with Remotion?
1. Check `remotion-tours/` project setup
2. Verify Node.js 18+ in workflow
3. Check Cloudinary upload permissions

## FAQ

**Q: Can I use both Creatomate and GitHub Actions?**
A: Yes! The code supports both. Use `USE_CREATOMATE=true` for Creatomate or `USE_GITHUB_ACTIONS=true` for GitHub Actions.

**Q: What happens if GitHub Actions is down?**
A: The app automatically falls back to local FFmpeg rendering or Cloudinary.

**Q: Can I customize the Remotion effects?**
A: Yes! Edit `remotion-tours/src/KenBurnsImage.tsx` to customize effects.

**Q: How do I add new effects?**
A: Add new effect types in `KenBurnsImage.tsx` and update the `effectTypes` array.

## Next Steps

1. ✅ Complete the migration
2. 🎬 Test video generation
3. 📊 Monitor GitHub Actions usage
4. 🎨 Customize Remotion effects as needed

---

Migration complete! Your real estate videos now have professional Ken Burns effects with full control and 2,000 free minutes per month! 🎉