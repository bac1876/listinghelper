#!/usr/bin/env python3
"""
Railway Log Analysis Tool
Helps extract and analyze download errors from Railway logs
"""

import re
import sys
from datetime import datetime
import json

print("""
=================================================================
Railway Log Analysis Tool - Download Error Checker
=================================================================

To get your Railway logs:
1. Go to: https://railway.com/project/18ac0b69-08d5-4a6a-a01a-fe1194e6ddd1/logs
2. Log in if needed
3. Look for any error messages, especially:
   - Download failures
   - File not found errors
   - Cloudinary access issues
   - Storage write errors
   - Video generation errors

Common error patterns to look for:
- "Download error:"
- "File not found"
- "Job not found"
- "Error downloading"
- "Failed to download"
- "Cloudinary error"
- "Storage error"
- "Permission denied"

Copy relevant log entries and paste them below:
""")

print("\nPaste Railway logs (press Ctrl+D or Ctrl+Z when done):")
print("=" * 60)

try:
    log_lines = []
    while True:
        try:
            line = input()
            log_lines.append(line)
        except EOFError:
            break
except KeyboardInterrupt:
    pass

log_text = '\n'.join(log_lines)

# Analyze logs
print("\n\nAnalyzing logs...")
print("=" * 60)

# Pattern definitions
error_patterns = {
    'download_error': r'download.*error|Download.*error|Download error:',
    'file_not_found': r'File not found|404.*download|job.*not found',
    'cloudinary_error': r'cloudinary.*error|Cloudinary.*fail',
    'storage_error': r'storage.*error|Storage.*fail|Permission denied',
    'video_generation': r'video.*fail|Video.*error|ffmpeg.*error',
    'job_timeout': r'timeout|Timeout|timed out',
    'memory_error': r'memory|Memory|OOM|out of memory'
}

# Find matches
found_errors = {}
for error_type, pattern in error_patterns.items():
    matches = re.findall(f'.*{pattern}.*', log_text, re.IGNORECASE | re.MULTILINE)
    if matches:
        found_errors[error_type] = matches

# Extract job IDs
job_ids = re.findall(r'job[_-]?([a-f0-9-]{36})', log_text, re.IGNORECASE)
unique_job_ids = list(set(job_ids))

# Extract timestamps
timestamps = re.findall(r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})', log_text)

# Report findings
print("\n📊 ANALYSIS RESULTS")
print("=" * 60)

if found_errors:
    print("\n🔴 ERRORS FOUND:")
    for error_type, matches in found_errors.items():
        print(f"\n{error_type.replace('_', ' ').title()} ({len(matches)} occurrences):")
        for i, match in enumerate(matches[:3]):  # Show first 3
            print(f"  {i+1}. {match.strip()}")
        if len(matches) > 3:
            print(f"  ... and {len(matches) - 3} more")
else:
    print("\n✅ No specific error patterns found in the logs")

if unique_job_ids:
    print(f"\n📋 AFFECTED JOB IDS ({len(unique_job_ids)}):")
    for job_id in unique_job_ids[:5]:
        print(f"  - {job_id}")
    if len(unique_job_ids) > 5:
        print(f"  ... and {len(unique_job_ids) - 5} more")

if timestamps:
    print(f"\n⏰ TIME RANGE:")
    print(f"  First error: {min(timestamps)}")
    print(f"  Last error: {max(timestamps)}")

# Recommendations
print("\n💡 RECOMMENDATIONS:")
print("=" * 60)

if 'download_error' in found_errors or 'file_not_found' in found_errors:
    print("""
1. DOWNLOAD/FILE ERRORS:
   - Check if files are being properly saved to storage
   - Verify job directories are created correctly
   - Ensure file permissions are correct
   - Check if cleanup is removing files too early
""")

if 'cloudinary_error' in found_errors:
    print("""
2. CLOUDINARY ERRORS:
   - Verify Cloudinary credentials are correct
   - Check API rate limits
   - Ensure network connectivity
   - Verify upload size limits
""")

if 'storage_error' in found_errors:
    print("""
3. STORAGE ERRORS:
   - Check available disk space on Railway
   - Verify storage directory permissions
   - Ensure /app/storage directory exists
   - Check file system quotas
""")

if 'video_generation' in found_errors:
    print("""
4. VIDEO GENERATION ERRORS:
   - Verify FFmpeg is installed correctly
   - Check memory limits for video processing
   - Ensure image formats are supported
   - Monitor timeout settings
""")

if 'memory_error' in found_errors or 'job_timeout' in found_errors:
    print("""
5. RESOURCE ERRORS:
   - Consider upgrading Railway plan for more resources
   - Implement file size limits
   - Use lower quality settings for large videos
   - Add progress monitoring
""")

# Save analysis
save_analysis = input("\nSave analysis to file? (y/n): ")
if save_analysis.lower() == 'y':
    analysis_file = f"railway_log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'errors_found': found_errors,
            'job_ids': unique_job_ids,
            'time_range': {
                'first': min(timestamps) if timestamps else None,
                'last': max(timestamps) if timestamps else None
            },
            'raw_log_lines': len(log_lines)
        }, f, indent=2)
    print(f"\n✅ Analysis saved to: {analysis_file}")

print("\n" + "=" * 60)
print("Analysis complete!")