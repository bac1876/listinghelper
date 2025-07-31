from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the blueprint from working_ken_burns.py
from working_ken_burns import virtual_tour_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Register the virtual tour blueprint
app.register_blueprint(virtual_tour_bp)

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