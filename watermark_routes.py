"""
Watermark API Routes
Handles watermark upload, management, and configuration endpoints
"""

from flask import Blueprint, request, jsonify, send_file
import os
import logging
from werkzeug.utils import secure_filename

from watermark_config import watermark_manager, WatermarkPosition

logger = logging.getLogger(__name__)

# Create watermark blueprint
watermark_bp = Blueprint('watermark', __name__, url_prefix='/api/watermark')

@watermark_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for watermark service"""
    return jsonify({
        'status': 'healthy',
        'service': 'watermark',
        'storage_path': watermark_manager.storage_dir,
        'storage_writable': os.access(watermark_manager.storage_dir, os.W_OK),
        'watermark_count': len(watermark_manager.list_watermarks())
    })

@watermark_bp.route('/upload', methods=['POST'])
def upload_watermark():
    """Upload a new watermark image"""
    try:
        # Check if file was uploaded
        if 'watermark' not in request.files:
            return jsonify({'error': 'No watermark file provided'}), 400
        
        file = request.files['watermark']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get configuration parameters
        position = request.form.get('position', WatermarkPosition.BOTTOM_RIGHT)
        opacity = float(request.form.get('opacity', 0.7))
        scale = float(request.form.get('scale', 0.1))
        margin_x = int(request.form.get('margin_x', 20))
        margin_y = int(request.form.get('margin_y', 20))
        duration = request.form.get('duration', 'full')
        
        # Validate position
        if position not in WatermarkPosition.ALL_POSITIONS:
            return jsonify({'error': f'Invalid position. Must be one of: {WatermarkPosition.ALL_POSITIONS}'}), 400
        
        # Validate numeric parameters
        if not (0.0 <= opacity <= 1.0):
            return jsonify({'error': 'Opacity must be between 0.0 and 1.0'}), 400
        
        if not (0.01 <= scale <= 0.5):
            return jsonify({'error': 'Scale must be between 0.01 and 0.5'}), 400
        
        if margin_x < 0 or margin_y < 0:
            return jsonify({'error': 'Margins must be non-negative'}), 400
        
        if duration not in ['full', 'start', 'end']:
            return jsonify({'error': 'Duration must be one of: full, start, end'}), 400
        
        # Upload watermark
        config = watermark_manager.upload_watermark(
            file_data=file,
            filename=secure_filename(file.filename),
            position=position,
            opacity=opacity,
            scale=scale,
            margin_x=margin_x,
            margin_y=margin_y,
            duration=duration
        )
        
        logger.info(f"Watermark uploaded successfully: {config.watermark_id}")
        
        return jsonify({
            'success': True,
            'watermark_id': config.watermark_id,
            'message': 'Watermark uploaded successfully',
            'config': config.to_dict()
        })
        
    except ValueError as e:
        logger.warning(f"Watermark validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Watermark upload error: {e}")
        return jsonify({'error': 'Upload failed'}), 500

@watermark_bp.route('/list', methods=['GET'])
def list_watermarks():
    """List all available watermarks"""
    try:
        watermarks = watermark_manager.list_watermarks()
        return jsonify({
            'success': True,
            'watermarks': [wm.to_dict() for wm in watermarks],
            'count': len(watermarks)
        })
    except Exception as e:
        logger.error(f"Error listing watermarks: {e}")
        return jsonify({'error': 'Failed to list watermarks'}), 500

@watermark_bp.route('/<watermark_id>', methods=['GET'])
def get_watermark(watermark_id):
    """Get specific watermark configuration"""
    try:
        config = watermark_manager.get_watermark(watermark_id)
        if not config:
            return jsonify({'error': 'Watermark not found'}), 404
        
        return jsonify({
            'success': True,
            'watermark': config.to_dict()
        })
    except Exception as e:
        logger.error(f"Error getting watermark {watermark_id}: {e}")
        return jsonify({'error': 'Failed to get watermark'}), 500

@watermark_bp.route('/<watermark_id>', methods=['PUT'])
def update_watermark(watermark_id):
    """Update watermark configuration"""
    try:
        config = watermark_manager.get_watermark(watermark_id)
        if not config:
            return jsonify({'error': 'Watermark not found'}), 404
        
        # Get update parameters
        update_data = {}
        
        if 'position' in request.json:
            position = request.json['position']
            if position not in WatermarkPosition.ALL_POSITIONS:
                return jsonify({'error': f'Invalid position. Must be one of: {WatermarkPosition.ALL_POSITIONS}'}), 400
            update_data['position'] = position
        
        if 'opacity' in request.json:
            opacity = float(request.json['opacity'])
            if not (0.0 <= opacity <= 1.0):
                return jsonify({'error': 'Opacity must be between 0.0 and 1.0'}), 400
            update_data['opacity'] = opacity
        
        if 'scale' in request.json:
            scale = float(request.json['scale'])
            if not (0.01 <= scale <= 0.5):
                return jsonify({'error': 'Scale must be between 0.01 and 0.5'}), 400
            update_data['scale'] = scale
        
        if 'margin_x' in request.json:
            margin_x = int(request.json['margin_x'])
            if margin_x < 0:
                return jsonify({'error': 'Margin X must be non-negative'}), 400
            update_data['margin_x'] = margin_x
        
        if 'margin_y' in request.json:
            margin_y = int(request.json['margin_y'])
            if margin_y < 0:
                return jsonify({'error': 'Margin Y must be non-negative'}), 400
            update_data['margin_y'] = margin_y
        
        if 'duration' in request.json:
            duration = request.json['duration']
            if duration not in ['full', 'start', 'end']:
                return jsonify({'error': 'Duration must be one of: full, start, end'}), 400
            update_data['duration'] = duration
        
        # Update configuration
        updated_config = watermark_manager.update_watermark_config(watermark_id, **update_data)
        
        logger.info(f"Watermark updated: {watermark_id}")
        
        return jsonify({
            'success': True,
            'message': 'Watermark updated successfully',
            'watermark': updated_config.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating watermark {watermark_id}: {e}")
        return jsonify({'error': 'Failed to update watermark'}), 500

@watermark_bp.route('/<watermark_id>', methods=['DELETE'])
def delete_watermark(watermark_id):
    """Delete a watermark"""
    try:
        success = watermark_manager.delete_watermark(watermark_id)
        if not success:
            return jsonify({'error': 'Watermark not found'}), 404
        
        logger.info(f"Watermark deleted: {watermark_id}")
        
        return jsonify({
            'success': True,
            'message': 'Watermark deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting watermark {watermark_id}: {e}")
        return jsonify({'error': 'Failed to delete watermark'}), 500

@watermark_bp.route('/<watermark_id>/preview', methods=['GET'])
def get_watermark_image(watermark_id):
    """Get watermark image file for preview"""
    try:
        config = watermark_manager.get_watermark(watermark_id)
        if not config or not config.filepath:
            return jsonify({'error': 'Watermark not found'}), 404
        
        if not os.path.exists(config.filepath):
            return jsonify({'error': 'Watermark file not found'}), 404
        
        return send_file(
            config.filepath,
            as_attachment=False,
            download_name=f"watermark_{watermark_id}.png"
        )
    except Exception as e:
        logger.error(f"Error serving watermark image {watermark_id}: {e}")
        return jsonify({'error': 'Failed to get watermark image'}), 500

@watermark_bp.route('/positions', methods=['GET'])
def get_available_positions():
    """Get list of available watermark positions"""
    return jsonify({
        'success': True,
        'positions': [
            {
                'value': pos,
                'label': pos.replace('-', ' ').title(),
                'description': _get_position_description(pos)
            }
            for pos in WatermarkPosition.ALL_POSITIONS
        ]
    })

def _get_position_description(position: str) -> str:
    """Get human-readable description for position"""
    descriptions = {
        WatermarkPosition.TOP_LEFT: 'Upper left corner of the video',
        WatermarkPosition.TOP_RIGHT: 'Upper right corner of the video',
        WatermarkPosition.TOP_CENTER: 'Top center of the video',
        WatermarkPosition.CENTER: 'Center of the video',
        WatermarkPosition.BOTTOM_LEFT: 'Lower left corner of the video',
        WatermarkPosition.BOTTOM_RIGHT: 'Lower right corner of the video (recommended)',
        WatermarkPosition.BOTTOM_CENTER: 'Bottom center of the video'
    }
    return descriptions.get(position, 'Custom position')

@watermark_bp.route('/test-overlay', methods=['POST'])
def test_watermark_overlay():
    """Test watermark overlay without generating full video"""
    try:
        data = request.get_json()
        watermark_id = data.get('watermark_id')
        
        if not watermark_id:
            return jsonify({'error': 'Watermark ID required'}), 400
        
        config = watermark_manager.get_watermark(watermark_id)
        if not config:
            return jsonify({'error': 'Watermark not found'}), 404
        
        # Generate FFmpeg filter for testing
        overlay_filter = config.get_ffmpeg_overlay_filter(1920, 1080)
        
        return jsonify({
            'success': True,
            'watermark_id': watermark_id,
            'ffmpeg_filter': overlay_filter,
            'config': config.to_dict(),
            'test_result': 'FFmpeg overlay filter generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error testing watermark overlay: {e}")
        return jsonify({'error': 'Failed to test watermark overlay'}), 500

@watermark_bp.route('/cleanup', methods=['POST'])
def cleanup_old_watermarks():
    """Clean up old watermarks (admin endpoint)"""
    try:
        # Only allow cleanup from localhost or with admin key
        if not _is_admin_request():
            return jsonify({'error': 'Unauthorized'}), 403
        
        days_old = int(request.json.get('days_old', 30))
        if days_old < 1:
            return jsonify({'error': 'Days old must be at least 1'}), 400
        
        deleted_count = watermark_manager.cleanup_old_watermarks(days_old)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} old watermarks',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up watermarks: {e}")
        return jsonify({'error': 'Failed to cleanup watermarks'}), 500

def _is_admin_request() -> bool:
    """Check if request is from admin (simple localhost check for now)"""
    # In production, you might want to use API keys or proper auth
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    return client_ip in ['127.0.0.1', '::1', 'localhost']