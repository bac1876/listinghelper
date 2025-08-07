"""
Production server runner using Waitress
This provides a stable, multi-threaded server for handling multiple image uploads
"""
import os
import sys
from waitress import serve
from main import app
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_production_server():
    """Run the Flask app with Waitress production server"""
    
    # Server configuration
    host = '0.0.0.0'
    port = int(os.environ.get('PORT', 5000))
    
    # Waitress configuration for handling large uploads
    # These settings are optimized for image upload handling
    config = {
        'host': host,
        'port': port,
        'threads': 6,  # Number of worker threads
        'connection_limit': 100,  # Max concurrent connections
        'cleanup_interval': 30,  # Cleanup abandoned connections every 30 seconds
        'channel_timeout': 120,  # Timeout for idle connections (2 minutes)
        'max_request_body_size': 104857600,  # 100MB max upload size
        'asyncore_use_poll': True,  # Better performance on Windows
    }
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Virtual Tour Generator - Production Server        ║
╠══════════════════════════════════════════════════════════╣
║  Server:     Waitress (Production-Ready)                  ║
║  Host:       {host:<45}║
║  Port:       {port:<45}║
║  Threads:    {config['threads']:<45}║
║  Max Upload: 100 MB                                       ║
║                                                            ║
║  Access at:  http://localhost:{port:<39}║
║                                                            ║
║  This server is optimized for handling multiple           ║
║  image uploads without crashing.                          ║
║                                                            ║
║  Press Ctrl+C to stop the server                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        logger.info(f"Starting Waitress server on {host}:{port}")
        serve(app, **config)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_production_server()