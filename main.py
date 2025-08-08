from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize and test ImageKit after loading env vars
from imagekit_integration import test_imagekit_initialization
imagekit_ready = test_imagekit_initialization()
if not imagekit_ready:
    print("=" * 60)
    print("WARNING: ImageKit not configured!")
    print("Using Cloudinary as fallback (100MB limit, 25 credits only)")
    print("To use ImageKit, ensure these env vars are set in Railway:")
    print("  - IMAGEKIT_PRIVATE_KEY")
    print("  - IMAGEKIT_PUBLIC_KEY")
    print("  - IMAGEKIT_URL_ENDPOINT")
    print("=" * 60)

# Import the blueprint - use GitHub Actions version if configured
use_github_actions = os.environ.get('USE_GITHUB_ACTIONS', 'false').lower() == 'true'
if use_github_actions and all([os.environ.get('GITHUB_TOKEN'), os.environ.get('GITHUB_OWNER'), os.environ.get('GITHUB_REPO')]):
    from working_ken_burns_github import virtual_tour_bp
    from webhook_handler import webhook_bp
else:
    from working_ken_burns import virtual_tour_bp
    webhook_bp = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure app for handling large uploads
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload
app.config['UPLOAD_FOLDER'] = 'temp_uploads'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    
@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status}")
    return response

# Register the virtual tour blueprint
app.register_blueprint(virtual_tour_bp)

# Register webhook blueprint if using GitHub Actions
if webhook_bp:
    app.register_blueprint(webhook_bp)
    logger.info("GitHub webhook handler registered at /api/webhook/github")

# Root route to serve the CSS3 Ken Burns frontend
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# Health check route at root level
@app.route('/health')
def health():
    return {'status': 'healthy', 'app': 'Virtual Tour Generator'}

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # For local development
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)