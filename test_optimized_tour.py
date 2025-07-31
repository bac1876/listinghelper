"""
Test the optimized virtual tour generator
"""
import os
import sys

# Set environment variable to use optimized tour
os.environ['USE_OPTIMIZED_TOUR'] = '1'

from ffmpeg_ken_burns import create_ken_burns_video

def test_optimized_tour():
    # Get test images
    test_images = [
        'test_images/living_room.jpg',
        'test_images/kitchen.jpg',
        'test_images/bedroom.jpg',
        'test_images/exterior.jpg'
    ]
    
    # Check if test images exist
    for img in test_images:
        if not os.path.exists(img):
            print(f"Test image not found: {img}")
            return
    
    output_path = 'test_optimized_tour.mp4'
    
    print("Testing optimized virtual tour generator...")
    try:
        result = create_ken_burns_video(test_images, output_path, 'test_job')
        print(f"Success! Video created at: {result}")
        print(f"File size: {os.path.getsize(result) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_tour()