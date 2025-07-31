"""
Test if the generated video is playable
"""
import cv2
import os

def test_video_playback(video_path):
    """Test if video can be opened and read"""
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return False
    
    print(f"Testing video: {video_path}")
    print(f"File size: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
    
    # Try to open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("ERROR: Cannot open video file")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video properties:")
    print(f"  FPS: {fps}")
    print(f"  Frame count: {frame_count}")
    print(f"  Resolution: {width}x{height}")
    print(f"  Duration: {frame_count / fps:.2f} seconds")
    
    # Try to read a few frames
    frames_read = 0
    while frames_read < min(5, frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        frames_read += 1
    
    cap.release()
    
    print(f"Successfully read {frames_read} frames")
    return frames_read > 0

if __name__ == "__main__":
    success = test_video_playback("test_imageio.mp4")
    if success:
        print("\nVideo is playable!")
    else:
        print("\nVideo is not playable!")