import os
import sys
import logging
import sqlite3
from flask import Flask, jsonify
from dotenv import load_dotenv

# Minimal logging configuration
logging.basicConfig(
    level=logging.ERROR, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
MAX_IMAGES = int(os.getenv('MAX_IMAGES', 1000000))
PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', 5.00))

# Robust upload folder path resolution
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Robust database path resolution
def get_writable_db_path():
    potential_paths = [
        '/tmp/database/payment_tracker.db',
        '/app/payment_tracker.db',
        os.path.join(os.getcwd(), 'payment_tracker.db'),
        '/tmp/payment_tracker.db'
    ]
    
    for path in potential_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            conn = sqlite3.connect(path)
            conn.close()
            return path
        except Exception:
            continue
    
    raise RuntimeError("No writable database path found")

# Get the best available database path
DB_PATH = get_writable_db_path()

# Minimal routes
@app.route('/')
def index():
    """Basic index route."""
    return jsonify({
        'status': 'online',
        'max_images': MAX_IMAGES,
        'price_per_image': PRICE_PER_IMAGE
    }), 200

@app.route('/health')
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'database_path': DB_PATH
    }), 200

# Error handler for 500 errors
@app.errorhandler(500)
def handle_500(error):
    """Custom error handler for server errors."""
    logger.error(f"Server Error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500

# Main block for development server
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
