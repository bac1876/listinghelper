#!/usr/bin/env python3
"""
Test ImageKit uploads directly to see what URLs are generated
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from imagekit_integration import get_imagekit
import requests

def test_imagekit_direct():
    """Test ImageKit uploads and URL generation."""
    
    print("=" * 60)
    print("ImageKit Direct Upload Test")
    print("=" * 60)
    
    # Get ImageKit instance
    try:
        imagekit = get_imagekit()
        if not imagekit:
            print("[ERROR] ImageKit not initialized")
            return
        print("[OK] ImageKit initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize ImageKit: {e}")
        return
    
    # List existing files in the tours/images folder
    print("\n" + "-" * 60)
    print("Listing existing files in /tours/images/:")
    print("-" * 60)
    
    try:
        # Use ImageKit SDK to list files
        from imagekitio.models.ListAndSearchFileRequestOptions import ListAndSearchFileRequestOptions
        
        options = ListAndSearchFileRequestOptions(
            path="/tours/images/",
            limit=5
        )
        
        result = imagekit.imagekit.list_files(options)
        
        if hasattr(result, 'response_metadata'):
            files = result.response_metadata.get('raw', [])
            print(f"Found {len(files)} files")
            
            for i, file_info in enumerate(files[:5], 1):
                file_url = file_info.get('url', 'No URL')
                file_name = file_info.get('name', 'Unknown')
                file_id = file_info.get('fileId', 'No ID')
                
                print(f"\n[{i}] {file_name}")
                print(f"    URL: {file_url}")
                print(f"    ID: {file_id}")
                
                # Test if URL is accessible
                if file_url and file_url != 'No URL':
                    try:
                        response = requests.head(file_url, timeout=5)
                        if response.status_code == 200:
                            print(f"    Access: [OK] Public")
                        else:
                            print(f"    Access: [FAIL] Status {response.status_code}")
                    except:
                        print(f"    Access: [ERROR] Cannot reach")
        else:
            print("No files found or could not list files")
            
    except Exception as e:
        print(f"[ERROR] Failed to list files: {e}")
    
    # Test uploading a small test image
    print("\n" + "-" * 60)
    print("Testing new upload:")
    print("-" * 60)
    
    try:
        # Create a small test image
        from PIL import Image
        import io
        import base64
        
        # Create a 100x100 red test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(img_bytes.read()).decode()
        
        # Upload to ImageKit
        print("Uploading test image to ImageKit...")
        
        from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
        
        options = UploadFileRequestOptions(
            file=img_base64,
            file_name="test_access_check.jpg",
            folder="/tours/images/",
            use_unique_file_name=True,
            is_private_file=False,  # Ensure it's public
            response_fields=["url", "fileId", "name", "size", "isPrivateFile"]
        )
        
        result = imagekit.imagekit.upload_file(options)
        
        if hasattr(result, 'url'):
            url = result.url
            file_id = result.file_id
            is_private = getattr(result, 'is_private_file', None)
            
            print(f"\n[SUCCESS] Upload completed")
            print(f"URL: {url}")
            print(f"File ID: {file_id}")
            print(f"Is Private: {is_private}")
            
            # Test accessibility
            print("\nTesting public access to uploaded file...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"[OK] File is publicly accessible")
                print(f"Content length: {len(response.content)} bytes")
            else:
                print(f"[FAIL] File not accessible - Status: {response.status_code}")
                
            # Try to get a public URL if needed
            if is_private:
                print("\n[WARNING] File was uploaded as private!")
                print("This is why GitHub Actions cannot access the images!")
        else:
            print(f"[ERROR] Upload failed: {result}")
            
    except Exception as e:
        print(f"[ERROR] Test upload failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imagekit_direct()