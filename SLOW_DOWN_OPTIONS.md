# Options to Slow Down the Virtual Tour Images

## Current Situation
The Creatomate template has fixed timing (12 seconds per image for a 60-second video). The timing is built into their template.

## Option 1: Try Duration Parameters (Quick Test)
I can add duration parameters to the Creatomate API call. This might work if their template supports it:

```python
modifications['duration'] = 120  # 2-minute video instead of 1 minute
# or
modifications['Photo-1.duration'] = 20  # 20 seconds per image
```

## Option 2: Use Local Video Generation (Full Control)
Switch back to the local ffmpeg generator which gives you complete control:
- Set image duration: 8-15 seconds per image
- Control transition speed
- Adjust Ken Burns effect speed
- Create videos of any length

To use this option, set in Railway:
```
USE_CREATOMATE=false
FORCE_PREMIUM_QUALITY=true
```

## Option 3: Different Creatomate Template
Browse Creatomate's template library for a real estate template with:
- Longer image display times
- Adjustable timing parameters
- Slower transitions

## Option 4: Custom Creatomate Template
Create your own template in Creatomate with:
- Custom timing controls
- Adjustable durations per image
- Your preferred transition speeds

## Recommendation
Let's try Option 1 first (adding duration parameters). If that doesn't work, Option 2 (local generation) gives you immediate control over timing with these settings:
- 8 seconds per image = relaxed pace
- 10 seconds per image = very slow
- 15 seconds per image = extremely slow

Would you like me to:
1. Try adding duration parameters to Creatomate?
2. Set up local generation with custom timing?
3. Help you find a different Creatomate template?