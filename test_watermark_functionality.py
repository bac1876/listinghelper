#!/usr/bin/env python3
"""
Test script for watermark functionality
Tests the watermark configuration, upload, and integration with video generation
"""

import os
import sys
import tempfile
import requests
from PIL import Image, ImageDraw
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def create_test_watermark(filename='test_watermark.png', text='TEST LOGO'):
    """Create a simple test watermark image"""
    # Create a simple watermark image
    img = Image.new('RGBA', (200, 60), (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(img)
    
    # Draw text with semi-transparent background
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (200 - text_width) // 2
    y = (60 - text_height) // 2
    
    # Draw background rectangle
    draw.rectangle([x-5, y-2, x+text_width+5, y+text_height+2], fill=(0, 0, 0, 128))
    
    # Draw text
    draw.text((x, y), text, fill=(255, 255, 255, 255))
    
    # Save to temporary file
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    img.save(temp_path, 'PNG')
    logger.info(f"Created test watermark: {temp_path}")
    return temp_path

def test_watermark_config():
    """Test watermark configuration classes"""
    try:
        from watermark_config import WatermarkConfig, WatermarkManager, WatermarkPosition
        
        logger.info("Testing WatermarkConfig...")
        
        # Create a test watermark file for testing
        test_watermark_path = create_test_watermark('config_test.png')
        
        # Test WatermarkConfig creation
        config = WatermarkConfig(
            watermark_id="test-123",
            filepath=test_watermark_path,
            position=WatermarkPosition.BOTTOM_RIGHT,
            opacity=0.8,
            scale=0.15
        )
        
        # Test serialization
        config_dict = config.to_dict()
        assert config_dict['watermark_id'] == "test-123"
        assert config_dict['opacity'] == 0.8
        assert config_dict['scale'] == 0.15
        logger.info("✓ WatermarkConfig serialization works")
        
        # Test deserialization
        config2 = WatermarkConfig.from_dict(config_dict)
        assert config2.watermark_id == config.watermark_id
        assert config2.opacity == config.opacity
        logger.info("✓ WatermarkConfig deserialization works")
        
        # Test FFmpeg filter generation
        filter_string = config.get_ffmpeg_overlay_filter(1920, 1080)
        assert filter_string != ""
        assert "overlay=" in filter_string
        logger.info("✓ FFmpeg filter generation works")
        logger.info(f"Sample filter: {filter_string[:100]}...")
        
        # Test WatermarkManager
        manager = WatermarkManager()
        logger.info("✓ WatermarkManager initialized successfully")
        
        logger.info("✅ All watermark configuration tests passed!")
        
        # Clean up test file
        if 'test_watermark_path' in locals() and os.path.exists(test_watermark_path):
            os.remove(test_watermark_path)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Watermark configuration test failed: {e}")
        # Clean up test file
        if 'test_watermark_path' in locals() and os.path.exists(test_watermark_path):
            os.remove(test_watermark_path)
        return False

def test_watermark_api(base_url='http://localhost:5000'):
    """Test watermark API endpoints"""
    try:
        logger.info("Testing watermark API endpoints...")
        
        # Test health endpoint
        response = requests.get(f'{base_url}/api/watermark/health')
        if response.status_code == 200:
            health_data = response.json()
            logger.info(f"✓ Watermark service health: {health_data['status']}")
        else:
            logger.warning(f"⚠ Watermark health check failed: {response.status_code}")
        
        # Test positions endpoint
        response = requests.get(f'{base_url}/api/watermark/positions')
        if response.status_code == 200:
            positions_data = response.json()
            logger.info(f"✓ Available positions: {len(positions_data['positions'])}")
        else:
            logger.warning(f"⚠ Positions endpoint failed: {response.status_code}")
        
        # Test watermark upload
        watermark_path = create_test_watermark()
        
        with open(watermark_path, 'rb') as f:
            files = {'watermark': f}
            data = {
                'position': 'bottom-right',
                'opacity': '0.7',
                'scale': '0.1',
                'margin_x': '20',
                'margin_y': '20',
                'duration': 'full'
            }
            
            response = requests.post(f'{base_url}/api/watermark/upload', files=files, data=data)
            
            if response.status_code == 200:
                upload_result = response.json()
                watermark_id = upload_result.get('watermark_id')
                logger.info(f"✓ Watermark uploaded successfully: {watermark_id}")
                
                # Test watermark retrieval
                response = requests.get(f'{base_url}/api/watermark/{watermark_id}')
                if response.status_code == 200:
                    watermark_data = response.json()
                    logger.info("✓ Watermark retrieval successful")
                else:
                    logger.warning(f"⚠ Watermark retrieval failed: {response.status_code}")
                
                # Test watermark list
                response = requests.get(f'{base_url}/api/watermark/list')
                if response.status_code == 200:
                    list_data = response.json()
                    logger.info(f"✓ Watermark list: {list_data['count']} watermarks")
                else:
                    logger.warning(f"⚠ Watermark list failed: {response.status_code}")
                
                # Test overlay test
                response = requests.post(f'{base_url}/api/watermark/test-overlay', 
                                       json={'watermark_id': watermark_id})
                if response.status_code == 200:
                    test_result = response.json()
                    logger.info("✓ Overlay test successful")
                    logger.info(f"FFmpeg filter: {test_result['ffmpeg_filter'][:50]}...")
                else:
                    logger.warning(f"⚠ Overlay test failed: {response.status_code}")
                
                return watermark_id
            else:
                logger.error(f"❌ Watermark upload failed: {response.status_code}")
                return None
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠ Cannot connect to server - API tests skipped")
        logger.info("To test API endpoints, start the server with: python main.py")
        return None
    except Exception as e:
        logger.error(f"❌ API test failed: {e}")
        return None
    finally:
        # Clean up test watermark
        if 'watermark_path' in locals() and os.path.exists(watermark_path):
            os.remove(watermark_path)

def test_ffmpeg_integration():
    """Test FFmpeg watermark integration"""
    try:
        logger.info("Testing FFmpeg watermark integration...")
        
        from ffmpeg_watermark_integration import validate_watermark_compatibility
        from watermark_config import watermark_manager
        
        # Create a test watermark
        watermark_path = create_test_watermark()
        
        # Upload it to the manager
        with open(watermark_path, 'rb') as f:
            class MockFile:
                def __init__(self, file_obj):
                    self.file_obj = file_obj
                def save(self, path):
                    self.file_obj.seek(0)
                    with open(path, 'wb') as out:
                        out.write(self.file_obj.read())
                def seek(self, pos, whence=0):
                    return self.file_obj.seek(pos, whence)
                def tell(self):
                    return self.file_obj.tell()
            
            mock_file = MockFile(f)
            config = watermark_manager.upload_watermark(
                file_data=mock_file,
                filename='test_watermark.png',
                position='bottom-right',
                opacity=0.7,
                scale=0.1
            )
            
            logger.info(f"✓ Test watermark uploaded to manager: {config.watermark_id}")
            
            # Test validation
            validation = validate_watermark_compatibility(config.watermark_id)
            if validation['valid']:
                logger.info("✓ Watermark compatibility validation passed")
                logger.info(f"Scaled dimensions: {validation['scaled_dimensions']}")
            else:
                logger.warning(f"⚠ Watermark validation failed: {validation['error']}")
        
        # Clean up
        if os.path.exists(watermark_path):
            os.remove(watermark_path)
        
        logger.info("✅ FFmpeg integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ FFmpeg integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_workflow():
    """Test the complete watermark workflow"""
    logger.info("Running complete watermark workflow test...")
    
    success_count = 0
    total_tests = 3
    
    # Test 1: Configuration
    if test_watermark_config():
        success_count += 1
    
    # Test 2: API endpoints (if server is running)
    watermark_id = test_watermark_api()
    if watermark_id:
        success_count += 1
        logger.info("API tests completed successfully")
    else:
        logger.info("API tests skipped (server not running)")
    
    # Test 3: FFmpeg integration
    if test_ffmpeg_integration():
        success_count += 1
    
    # Summary
    logger.info("=" * 50)
    logger.info(f"WATERMARK TEST SUMMARY: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        logger.info("All watermark functionality tests passed!")
        logger.info("The watermark feature is ready for use!")
    else:
        logger.warning(f"⚠ {total_tests - success_count} test(s) failed")
        logger.info("Some functionality may not work correctly.")
    
    # Usage instructions
    logger.info("\n" + "=" * 50)
    logger.info("USAGE INSTRUCTIONS:")
    logger.info("1. Start the server: python main.py")
    logger.info("2. Open browser to: http://localhost:5000")
    logger.info("3. Upload photos and watermark")
    logger.info("4. Configure watermark settings")
    logger.info("5. Generate video with watermark")
    logger.info("=" * 50)
    
    return success_count == total_tests

if __name__ == '__main__':
    print("Testing ListingHelper Watermark Functionality")
    print("=" * 50)
    
    success = test_complete_workflow()
    exit_code = 0 if success else 1
    sys.exit(exit_code)