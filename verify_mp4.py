#!/usr/bin/env python3
"""
Verify MP4 files are valid
"""

import os
import glob

def verify_mp4_file(filepath):
    """Check if file is a valid MP4"""
    if not os.path.exists(filepath):
        return False, "File not found"
    
    size = os.path.getsize(filepath)
    if size == 0:
        return False, "File is empty"
    
    # Read file header
    with open(filepath, 'rb') as f:
        header = f.read(32)
        
        # MP4 files have 'ftyp' box typically at offset 4
        if b'ftyp' in header[:12]:
            # Check for common MP4 brands
            if any(brand in header for brand in [b'isom', b'mp42', b'mp41', b'M4V ']):
                return True, f"Valid MP4 (size: {size/1024/1024:.2f} MB)"
        
        # Sometimes ftyp is at beginning
        if header.startswith(b'ftyp'):
            return True, f"Valid MP4 (size: {size/1024/1024:.2f} MB)"
    
    return False, "Not a valid MP4 file"

# Find all test video files
video_files = glob.glob("test_video*.mp4")

print(f"Found {len(video_files)} video file(s) to verify:\n")

for video_file in video_files:
    is_valid, message = verify_mp4_file(video_file)
    status = "VALID" if is_valid else "INVALID"
    print(f"{video_file}:")
    print(f"  Status: {status}")
    print(f"  {message}")
    
    if is_valid:
        # Show first 64 bytes in hex for verification
        with open(video_file, 'rb') as f:
            data = f.read(64)
            print(f"  Header: {data[:32].hex()}")
            print()

# Summary
valid_count = sum(1 for f in video_files if verify_mp4_file(f)[0])
print(f"\nSummary: {valid_count}/{len(video_files)} valid MP4 files")