import os
import sys
import logging
import sqlite3
from flask import Flask, jsonify
from dotenv import load_dotenv

# Disable all logging
logging.getLogger().addHandler(logging.NullHandler())
logging.getLogger().setLevel(logging.CRITICAL)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration with minimal error handling
MAX_IMAGES = int(os.getenv('MAX_IMAGES', 1000000))
PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', 5.00))

# Robust upload folder path resolution
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Minimal database path resolution
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
    
    sys.exit(1)

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

# Minimal error handler
@app.errorhandler(500)
def handle_500(error):
    """Minimal error handler."""
    return jsonify({
        'error': 'Internal Server Error'
    }), 500

# Main block for development server
if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
