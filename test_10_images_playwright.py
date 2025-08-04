import asyncio
import os
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright
import requests

async def test_10_images():
    """Test uploading 10 images and verify all are used in the video"""
    
    # Start Flask app in a separate process
    import subprocess
    flask_process = subprocess.Popen(['py', 'main.py'])
    
    # Wait for Flask to start
    print("Waiting for Flask app to start...")
    time.sleep(5)
    
    # Check if Flask is running
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:5000')
            if response.status_code == 200:
                print("Flask app is running!")
                break
        except:
            print(f"Waiting for Flask... attempt {i+1}/{max_retries}")
            time.sleep(2)
    else:
        print("Flask app failed to start")
        flask_process.terminate()
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to the app
            print("\n1. Navigating to application...")
            await page.goto('http://localhost:5000')
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            await page.screenshot(path=f'test_10_images_initial_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
            # Create 10 test images
            print("\n2. Creating 10 test images...")
            test_images_dir = 'test_images_10'
            os.makedirs(test_images_dir, exist_ok=True)
            
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            image_paths = []
            for i in range(10):
                # Create colorful test image with number
                img = Image.new('RGB', (1920, 1080), 
                               color=(random.randint(50, 255), 
                                     random.randint(50, 255), 
                                     random.randint(50, 255)))
                draw = ImageDraw.Draw(img)
                
                # Try to use a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("arial.ttf", 200)
                except:
                    font = ImageFont.load_default()
                
                # Draw image number
                text = f"Image {i+1}"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((1920 - text_width) // 2, (1080 - text_height) // 2)
                draw.text(position, text, fill='white', font=font)
                
                # Add border
                draw.rectangle([0, 0, 1919, 1079], outline='white', width=10)
                
                image_path = os.path.join(test_images_dir, f'test_image_{i+1:02d}.jpg')
                img.save(image_path, quality=95)
                image_paths.append(os.path.abspath(image_path))
                print(f"Created: {image_path}")
            
            # Wait for file input to be available
            print("\n3. Waiting for file input...")
            file_input = await page.wait_for_selector('input[type="file"]', timeout=10000)
            
            # Upload all 10 images
            print("\n4. Uploading 10 images...")
            await file_input.set_files(image_paths)
            
            # Wait for images to be processed
            await page.wait_for_timeout(2000)
            
            # Take screenshot after upload
            await page.screenshot(path=f'test_10_images_uploaded_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
            # Fill in property details
            print("\n5. Filling property details...")
            await page.fill('#address', '123 Test Street')
            await page.fill('#city', 'Test City, CA')
            await page.fill('#details', 'Beautiful 10-room mansion')
            
            # Click generate button
            print("\n6. Clicking generate button...")
            generate_button = await page.wait_for_selector('button:has-text("Generate Virtual Tour")', timeout=5000)
            await generate_button.click()
            
            # Monitor the generation process
            print("\n7. Monitoring video generation...")
            start_time = time.time()
            
            # Wait for either success or error
            result = await page.wait_for_selector(
                'text=/Generated video URL:|Error generating video/',
                timeout=300000  # 5 minutes timeout
            )
            
            generation_time = time.time() - start_time
            print(f"\nGeneration completed in {generation_time:.1f} seconds")
            
            # Take final screenshot
            await page.screenshot(path=f'test_10_images_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
            # Check if video was generated successfully
            video_url_element = await page.query_selector('a[href*="cloudinary.com"]')
            if video_url_element:
                video_url = await video_url_element.get_attribute('href')
                print(f"\n✅ SUCCESS: Video generated with URL: {video_url}")
                
                # Download and analyze the video
                print("\n8. Downloading video for analysis...")
                video_response = requests.get(video_url)
                video_filename = f'test_10_images_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
                with open(video_filename, 'wb') as f:
                    f.write(video_response.content)
                
                # Analyze video with OpenCV
                import cv2
                cap = cv2.VideoCapture(video_filename)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                print(f"\nVideo Analysis:")
                print(f"- Duration: {duration:.1f} seconds")
                print(f"- Frame count: {frame_count}")
                print(f"- FPS: {fps}")
                print(f"- Expected duration (10 images × 8 seconds): 80 seconds")
                
                # Sample frames to detect scene changes
                print("\n9. Detecting distinct images in video...")
                scenes = []
                prev_frame = None
                scene_start = 0
                frame_interval = int(fps * 2)  # Check every 2 seconds
                
                for i in range(0, frame_count, frame_interval):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if prev_frame is not None:
                        # Calculate difference
                        diff = cv2.absdiff(frame, prev_frame)
                        mean_diff = diff.mean()
                        
                        # Detect scene change
                        if mean_diff > 30:
                            scene_duration = (i - scene_start) / fps
                            if scene_duration > 3:  # Minimum scene duration
                                scenes.append({
                                    'start': scene_start / fps,
                                    'end': i / fps,
                                    'duration': scene_duration
                                })
                            scene_start = i
                    
                    prev_frame = frame.copy()
                
                # Add last scene
                if scene_start < frame_count - fps:
                    scenes.append({
                        'start': scene_start / fps,
                        'end': duration,
                        'duration': duration - (scene_start / fps)
                    })
                
                cap.release()
                
                print(f"\nDetected {len(scenes)} distinct scenes:")
                for i, scene in enumerate(scenes):
                    print(f"  Scene {i+1}: {scene['start']:.1f}s - {scene['end']:.1f}s (duration: {scene['duration']:.1f}s)")
                
                # Verify results
                if len(scenes) >= 10:
                    print(f"\n✅ SUCCESS: All 10 images appear to be in the video!")
                elif len(scenes) >= 8:
                    print(f"\n⚠️ PARTIAL SUCCESS: Found {len(scenes)} scenes (expected 10)")
                else:
                    print(f"\n❌ ISSUE DETECTED: Only {len(scenes)} scenes found (expected 10)")
                
                # Save test results
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'success': len(scenes) >= 10,
                    'video_url': video_url,
                    'video_duration': duration,
                    'frame_count': frame_count,
                    'fps': fps,
                    'scenes_detected': len(scenes),
                    'scenes': scenes,
                    'expected_duration': 80,
                    'actual_duration': duration
                }
                
                with open(f'test_10_images_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
                    json.dump(results, f, indent=2)
                
                return results
                
            else:
                print("\n❌ FAILED: No video URL found")
                error_element = await page.query_selector('text=/Error/')
                if error_element:
                    error_text = await error_element.text_content()
                    print(f"Error: {error_text}")
                
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            await page.screenshot(path=f'test_10_images_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
        finally:
            await browser.close()
            
            # Terminate Flask app
            print("\nTerminating Flask app...")
            flask_process.terminate()
            flask_process.wait()

if __name__ == "__main__":
    asyncio.run(test_10_images())