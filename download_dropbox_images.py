"""
Download real estate images from Dropbox for testing
"""
import os
import requests
import time

def download_dropbox_images():
    """Download images from the Dropbox shared folder"""
    
    # Create directory for test images
    os.makedirs('real_test_images', exist_ok=True)
    
    # Convert Dropbox link to direct download link
    # Change dl=0 to dl=1 for direct download
    base_url = "https://www.dropbox.com/scl/fo/65qwwvm05syiebxft76xu/ABP1BsU02m-VWTjXtnnGwdc?rlkey=q00uulzkk6j8r2bo27u5u2eb8&dl=1"
    
    print("Attempting to download images from Dropbox...")
    
    try:
        # Download the zip file (Dropbox usually provides folders as zip)
        response = requests.get(base_url, stream=True)
        
        if response.status_code == 200:
            # Save as zip file
            zip_path = 'real_test_images/dropbox_images.zip'
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded zip file: {zip_path}")
            
            # Extract the zip file
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('real_test_images')
            
            print("Images extracted successfully")
            
            # List all extracted images
            image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
            images = []
            
            for root, dirs, files in os.walk('real_test_images'):
                for file in files:
                    if any(file.endswith(ext) for ext in image_extensions):
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path) / (1024 * 1024)  # Size in MB
                        images.append((file, full_path, size))
                        print(f"Found: {file} ({size:.2f} MB)")
            
            print(f"\nTotal images found: {len(images)}")
            return images
            
        else:
            print(f"Failed to download: Status {response.status_code}")
            # Fallback: Use existing test images if available
            return use_existing_images()
            
    except Exception as e:
        print(f"Error downloading from Dropbox: {e}")
        return use_existing_images()

def use_existing_images():
    """Use existing test images as fallback"""
    print("\nUsing existing test images as fallback...")
    
    # Check for any existing test images
    test_dirs = ['test_images', 'test-images', 'test_images_10']
    images = []
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            for file in os.listdir(test_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_path = os.path.join(test_dir, file)
                    size = os.path.getsize(full_path) / (1024 * 1024)
                    images.append((file, full_path, size))
                    print(f"Found existing: {file} ({size:.2f} MB)")
    
    return images

if __name__ == "__main__":
    images = download_dropbox_images()
    print(f"\nReady for testing with {len(images)} images")
    
    # Save image list for tests
    with open('real_test_images/image_list.txt', 'w') as f:
        for name, path, size in images:
            f.write(f"{name}|{path}|{size}\n")
    
    print("Image list saved to real_test_images/image_list.txt")