"""
Debug script to analyze how many images are actually in the generated video
"""
import cv2
import os
import sys
import numpy as np
from collections import defaultdict

def analyze_video(video_path):
    """Analyze a video to detect distinct scenes/images"""
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"Video Analysis for: {video_path}")
    print(f"FPS: {fps}")
    print(f"Total frames: {frame_count}")
    print(f"Duration: {duration:.2f} seconds")
    print("-" * 50)
    
    # Analyze frames to detect scene changes
    prev_frame = None
    scene_changes = []
    frame_idx = 0
    significant_changes = []
    
    # Sample every 30th frame for efficiency
    sample_rate = 30
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % sample_rate == 0:
            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # Calculate difference between frames
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)
                
                # Detect significant changes (scene changes)
                if mean_diff > 30:  # Threshold for scene change
                    scene_time = frame_idx / fps
                    scene_changes.append((frame_idx, scene_time, mean_diff))
                    print(f"Scene change detected at frame {frame_idx} ({scene_time:.2f}s) - difference: {mean_diff:.2f}")
                    
                    # Save a thumbnail of the new scene
                    thumbnail_path = f"scene_{len(scene_changes)}_frame_{frame_idx}.jpg"
                    cv2.imwrite(thumbnail_path, frame)
                    print(f"  Saved thumbnail: {thumbnail_path}")
            
            prev_frame = gray
        
        frame_idx += 1
        
        # Progress indicator
        if frame_idx % 300 == 0:
            progress = (frame_idx / frame_count) * 100
            print(f"Progress: {progress:.1f}%")
    
    cap.release()
    
    print("\n" + "=" * 50)
    print(f"Total distinct scenes detected: {len(scene_changes) + 1}")  # +1 for the first scene
    print("=" * 50)
    
    # Estimate images based on scene duration
    if scene_changes:
        print("\nScene durations:")
        prev_time = 0
        for i, (frame, time, diff) in enumerate(scene_changes):
            duration = time - prev_time
            print(f"  Scene {i+1}: {duration:.2f} seconds (from {prev_time:.2f}s to {time:.2f}s)")
            prev_time = time
        # Last scene
        final_duration = (frame_count / fps) - prev_time
        print(f"  Scene {len(scene_changes)+1}: {final_duration:.2f} seconds (from {prev_time:.2f}s to end)")

def analyze_recent_videos():
    """Find and analyze recent video files"""
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    current_dir = os.getcwd()
    
    print(f"Searching for videos in: {current_dir}")
    print("-" * 50)
    
    videos_found = []
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                file_path = os.path.join(root, file)
                # Skip node_modules and other unnecessary directories
                if 'node_modules' not in file_path and '.git' not in file_path:
                    videos_found.append(file_path)
    
    if not videos_found:
        print("No video files found in current directory")
        return
    
    print(f"Found {len(videos_found)} video files:")
    for i, video in enumerate(videos_found[-10:]):  # Show last 10
        print(f"{i+1}. {os.path.relpath(video)}")
    
    print("\nAnalyzing most recent video...")
    # Sort by modification time and analyze the most recent
    videos_found.sort(key=lambda x: os.path.getmtime(x))
    most_recent = videos_found[-1]
    print(f"\nAnalyzing: {os.path.relpath(most_recent)}")
    print("=" * 50)
    analyze_video(most_recent)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Analyze specific video
        analyze_video(sys.argv[1])
    else:
        # Analyze recent videos
        analyze_recent_videos()