from flask import Flask, render_template, send_from_directory, request
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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