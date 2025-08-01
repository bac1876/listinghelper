"""
Check the duration of both test videos to see timing differences
"""
import subprocess
import json

def get_video_duration(url, name):
    """Get video duration using ffprobe"""
    try:
        # Use ffprobe to get video info
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    duration = float(stream.get('duration', 0))
                    print(f"{name} Template Duration: {duration:.1f} seconds")
                    if duration > 0:
                        # Estimate per-image duration
                        num_images = 5 if 'Original' in name else 4
                        per_image = duration / num_images
                        print(f"  Approximately {per_image:.1f} seconds per image")
                    return duration
        print(f"Could not get duration for {name}")
    except Exception as e:
        print(f"Error checking {name}: {e}")
        print("Make sure ffmpeg/ffprobe is installed")
    return None

print("Checking video durations...")
print("="*60)

# Check both videos
new_duration = get_video_duration(
    "https://f002.backblazeb2.com/file/creatomate-c8xg3hsxdu/fca7c0b5-c018-49b7-a34f-e148d65cdf5e.mp4",
    "New"
)

original_duration = get_video_duration(
    "https://f002.backblazeb2.com/file/creatomate-c8xg3hsxdu/db5f129b-813b-4122-81b9-298196061a28.mp4", 
    "Original"
)

print("\n" + "="*60)
print("TIMING COMPARISON:")
if new_duration and original_duration:
    if new_duration > original_duration:
        print(f"New template is {new_duration - original_duration:.1f} seconds LONGER (slower)")
    elif original_duration > new_duration:
        print(f"Original template is {original_duration - new_duration:.1f} seconds LONGER (slower)")
    else:
        print("Both templates have the same duration")