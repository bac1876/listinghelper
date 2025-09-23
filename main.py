from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize storage backend (Bunny.net only)
from storage_adapter import test_storage_initialization
storage_ready, backend_name = test_storage_initialization()

if storage_ready:
    print("=" * 60)
    print(f"[OK] Storage backend initialized: {backend_name.upper()}")
    if backend_name == 'bunnynet':
        print("  Using Bunny.net - No video transformation limits!")
    else:
        print(f"  Unknown backend: {backend_name}")
    print("=" * 60)
else:
    error_message = (
        'Storage backend not configured. Configure Bunny.net credentials '
        '(BUNNY_STORAGE_ZONE_NAME, BUNNY_ACCESS_KEY, BUNNY_PULL_ZONE_URL, optional BUNNY_REGION).'
    )
    print("=" * 60)
    print("ERROR: No storage backend configured!")
    print("Please configure Bunny.net storage:")
    print("")
    print("Required environment variables:")
    print("  - BUNNY_STORAGE_ZONE_NAME")
    print("  - BUNNY_ACCESS_KEY")
    print("  - BUNNY_PULL_ZONE_URL")
    print("  - BUNNY_REGION (optional, defaults to 'ny')")
    print("")
    print("ImageKit has been removed due to transformation limit issues.")
    print("=" * 60)
    raise RuntimeError(error_message)

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
    logger.info("Request: %s %s", request.method, request.path)
    if request.content_length:
        logger.debug("Payload bytes: %s", request.content_length)
    
@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status}")
    return response

# Register the virtual tour blueprint
app.register_blueprint(virtual_tour_bp)

# Register watermark blueprint
from watermark_routes import watermark_bp
app.register_blueprint(watermark_bp)
logger.info("Watermark API registered at /api/watermark")

# Register webhook blueprint if using GitHub Actions
if webhook_bp:
    app.register_blueprint(webhook_bp)
    logger.info("GitHub webhook handler registered at /api/webhook/github")

# Root route to serve the CSS3 Ken Burns frontend
@app.route('/')
def index():
    response = send_from_directory('static', 'index.html')
    # Disable caching to ensure latest version is served
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Health check route at root level
@app.route('/health')
def health():
    return {'status': 'healthy', 'app': 'Virtual Tour Generator'}

# Version check route to verify deployment
@app.route('/api/version')
def version():
    import datetime
    
    # Check if the fixed GitHub Actions integration is present
    has_fixed_github = False
    try:
        from github_actions_integration import GitHubActionsIntegration
        gh = GitHubActionsIntegration()
        # Check if the fixed method exists (with job_to_run_mapping)
        has_fixed_github = hasattr(gh, 'job_to_run_mapping')
    except:
        pass
    
    return {
        'version': '1.0.3',
        'deployment_time': datetime.datetime.now().isoformat(),
        'github_actions_enabled': use_github_actions,
        'github_actions_fixed': has_fixed_github,
        'storage_backend': backend_name if storage_ready else None,
        'storage_ready': storage_ready,
        'features': {
            'workflow_status_fix': has_fixed_github,
            'job_run_mapping': has_fixed_github
        }
    }

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # For local development only
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
