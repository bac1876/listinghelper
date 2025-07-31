"""
Fix for video codec issues - ensure proper codec and container compatibility
"""
import os
import cv2
import logging

logger = logging.getLogger(__name__)

def get_working_video_writer(output_path, fps, width, height):
    """
    Get a working video writer with proper codec/container compatibility
    """
    # For MP4 files, use these codec combinations
    if output_path.lower().endswith('.mp4'):
        codec_options = [
            # Most compatible MP4 codecs
            ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),  # MPEG-4 Part 2
            ('MP42', cv2.VideoWriter_fourcc(*'MP42')),  # MPEG-4.2
            ('DIV3', cv2.VideoWriter_fourcc(*'DIV3')),  # DivX 3
            ('DIVX', cv2.VideoWriter_fourcc(*'DIVX')),  # DivX
            ('FMP4', cv2.VideoWriter_fourcc(*'FMP4')),  # FFmpeg MPEG-4
        ]
    else:
        # For AVI files, use these codecs
        output_path = output_path.rsplit('.', 1)[0] + '.avi'
        codec_options = [
            ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
            ('MJPG', cv2.VideoWriter_fourcc(*'MJPG')),
            ('DIVX', cv2.VideoWriter_fourcc(*'DIVX')),
        ]
    
    for codec_name, fourcc in codec_options:
        try:
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
            if writer.isOpened():
                # Test write a black frame
                test_frame = cv2.imread(cv2.samples.findFile("starry_night.jpg"))
                if test_frame is None:
                    import numpy as np
                    test_frame = np.zeros((height, width, 3), dtype=np.uint8)
                else:
                    test_frame = cv2.resize(test_frame, (width, height))
                
                success = writer.write(test_frame)
                if success:
                    logger.info(f"Successfully initialized video writer with codec: {codec_name}")
                    # Reset writer for actual use
                    writer.release()
                    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
                    return writer, output_path
                else:
                    writer.release()
            else:
                if writer:
                    writer.release()
        except Exception as e:
            logger.warning(f"Failed with codec {codec_name}: {e}")
            continue
    
    # Last resort - try uncompressed AVI
    if not output_path.endswith('.avi'):
        output_path = output_path.rsplit('.', 1)[0] + '.avi'
    
    fourcc = cv2.VideoWriter_fourcc(*'RGBA')  # Uncompressed
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height), True)
    if writer.isOpened():
        logger.warning("Using uncompressed AVI format as last resort")
        return writer, output_path
    
    return None, None

# Export function
__all__ = ['get_working_video_writer']