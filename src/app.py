import os
import uuid
import requests
import json
import logging
import sys
import socket
import traceback
from flask import Flask, render_template, request, jsonify
from PIL import Image
from dotenv import load_dotenv
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Outputs to console
        logging.FileHandler('/tmp/app.log', mode='w')  # Outputs to file, overwrite each time
    ]
)
logger = logging.getLogger(__name__)

# Comprehensive network information logging
def log_comprehensive_network_info():
    try:
        logger.info("=== COMPREHENSIVE NETWORK INFORMATION ===")
        
        # Get local IP addresses
        try:
            local_ips = socket.gethostbyname_ex(socket.gethostname())[2]
            logger.info(f"Local IP Addresses: {local_ips}")
        except Exception as ip_error:
            logger.error(f"Could not retrieve local IP addresses: {ip_error}")
        
        # Additional system network information
        logger.info(f"Hostname: {socket.gethostname()}")
        
        try:
            # Try to get external IP
            external_ip = requests.get('https://api.ipify.org').text
            logger.info(f"External IP: {external_ip}")
        except Exception as ip_error:
            logger.error(f"Could not retrieve external IP: {ip_error}")
        
        # Environment variables related to networking
        logger.info(f"PORT environment variable: {os.getenv('PORT', 'Not set')}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        logger.info("=== END NETWORK INFORMATION ===")
    except Exception as e:
        logger.error(f"Comprehensive network logging failed: {e}")

# Comprehensive startup checks and logging
def perform_startup_checks():
    """Perform comprehensive checks during application startup."""
    try:
        # Check environment variables
        required_env_vars = [
            'UPLOAD_FOLDER', 
            'DATABASE_PATH', 
            'MAX_IMAGES', 
            'PRICE_PER_IMAGE'
        ]
        
        for var in required_env_vars:
            value = os.getenv(var)
            if value is None:
                logger.warning(f"Environment variable {var} is not set!")
        
        # Check upload folder
        upload_folder = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        if not os.access(upload_folder, os.W_OK):
            logger.error(f"Cannot write to upload folder: {upload_folder}")
        
        # Check database path
        database_path = os.getenv('DATABASE_PATH', '/tmp/database/payment_tracker.db')
        database_dir = os.path.dirname(database_path)
        os.makedirs(database_dir, exist_ok=True)
        
        # Attempt database connection
        try:
            conn = sqlite3.connect(database_path)
            conn.close()
            logger.info(f"Successfully connected to database at {database_path}")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
        
        # Log system information
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"Current Working Directory: {os.getcwd()}")
        logger.info(f"System Path: {sys.path}")
        
    except Exception as startup_error:
        logger.critical(f"Startup check failed: {startup_error}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

# Load environment variables
load_dotenv()

# Log system info early
log_comprehensive_network_info()

# Perform startup checks
perform_startup_checks()

app = Flask(__name__)

# Configuration
MAX_IMAGES = int(os.getenv('MAX_IMAGES', 1000000))
PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', 5.00))
USDC_WALLET_ADDRESS = os.getenv('USDC_WALLET_ADDRESS')
ADMIN_WALLET_ADDRESS = os.getenv('ADMIN_WALLET_ADDRESS')

# Robust upload folder path resolution
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Robust database path resolution with multiple fallback options
def get_writable_db_path():
    # Potential database paths in order of preference
    potential_paths = [
        '/tmp/database/payment_tracker.db',  # First choice
        '/app/payment_tracker.db',           # Render app directory
        os.path.join(os.getcwd(), 'payment_tracker.db'),  # Current working directory
        '/tmp/payment_tracker.db'            # Last resort temp directory
    ]
    
    for path in potential_paths:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Test database connection
            conn = sqlite3.connect(path)
            conn.close()
            
            logger.info(f"Using database path: {path}")
            return path
        except Exception as e:
            logger.warning(f"Cannot use path {path}: {e}")
    
    # If all paths fail, raise a critical error
    error_msg = "Unable to find a writable database path"
    logger.critical(error_msg)
    raise RuntimeError(error_msg)

# Get the best available database path
DB_PATH = get_writable_db_path()

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Initialize SQLite database for tracking payments
def init_db():
    try:
        # Open connection 
        conn = sqlite3.connect(DB_PATH)
        
        # Create table with error handling
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE,
                amount REAL,
                wallet_address TEXT,
                status TEXT,
                image_filename TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commit and close connection
        conn.commit()
        conn.close()
        
        # Log successful initialization
        logger.info(f"Database initialized at {DB_PATH}")
        
    except Exception as e:
        # Detailed error logging
        logger.error(f"Database initialization failed: {e}")
        logger.error(f"DB Path: {DB_PATH}")
        raise

# Call init_db during app startup
init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_payment(tx_hash, wallet_address):
    # Placeholder for blockchain transaction verification
    try:
        # Open connection 
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if transaction is already processed
        c.execute('SELECT * FROM payments WHERE tx_hash = ?', (tx_hash,))
        if c.fetchone():
            conn.close()
            logger.warning(f"Duplicate transaction hash: {tx_hash}")
            return False
        
        # Simulate successful payment verification
        c.execute('''
            INSERT INTO payments (tx_hash, amount, wallet_address, status) 
            VALUES (?, ?, ?, ?)
        ''', (tx_hash, PRICE_PER_IMAGE, wallet_address, 'verified'))
        
        conn.commit()
        conn.close()
        logger.info(f"Payment verified for tx_hash: {tx_hash}")
        
        return True
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        return False

@app.route('/')
def index():
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Safely list uploaded images
        try:
            uploaded_images = os.listdir(UPLOAD_FOLDER)
        except Exception as e:
            logger.warning(f"Could not list uploaded images: {e}")
            uploaded_images = []
        
        return render_template('index.html', 
                               images=uploaded_images, 
                               max_images=MAX_IMAGES,
                               price_per_image=PRICE_PER_IMAGE,
                               usdc_wallet_address=USDC_WALLET_ADDRESS)
    except Exception as e:
        logger.error(f"Index route failed: {e}")
        return "Server error", 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment_route():
    try:
        data = request.json
        tx_hash = data.get('tx_hash')
        wallet_address = data.get('wallet_address')
        
        if not tx_hash or not wallet_address:
            logger.warning("Missing transaction hash or wallet address")
            return jsonify({'error': 'Missing transaction hash or wallet address'}), 400
        
        if verify_payment(tx_hash, wallet_address):
            return jsonify({'status': 'Payment verified', 'ready_to_upload': True})
        else:
            return jsonify({'status': 'Payment verification failed'}), 400
    except Exception as e:
        logger.error(f"Payment verification route failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            logger.warning("No file part in upload request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("No selected file in upload request")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Check total number of images
            if len(os.listdir(UPLOAD_FOLDER)) >= MAX_IMAGES:
                logger.warning("Maximum number of images reached")
                return jsonify({'error': 'Maximum number of images reached'}), 400
            
            # Verify payment before upload
            tx_hash = request.form.get('tx_hash')
            wallet_address = request.form.get('wallet_address')
            
            if not tx_hash or not wallet_address:
                logger.warning("Payment not verified in upload request")
                return jsonify({'error': 'Payment not verified'}), 400
            
            # Verify payment
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM payments WHERE tx_hash = ? AND status = "verified"', (tx_hash,))
            payment_record = c.fetchone()
            conn.close()
            
            if not payment_record:
                logger.warning(f"Payment not verified for tx_hash: {tx_hash}")
                return jsonify({'error': 'Payment not verified'}), 400
            
            # Generate unique filename
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save file
            file.save(filepath)
            
            # Optional: Resize image to a standard size
            with Image.open(filepath) as img:
                img.thumbnail((800, 800))
                img.save(filepath)
            
            # Update payment record with image filename
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE payments SET image_filename = ? WHERE tx_hash = ?', (filename, tx_hash))
            conn.commit()
            conn.close()
            
            logger.info(f"Image uploaded successfully: {filename}")
            return jsonify({'success': True, 'filename': filename}), 200
        
        logger.warning("File type not allowed in upload")
        return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        logger.error(f"Upload route failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Add a simple health check route
@app.route('/health')
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'max_images': MAX_IMAGES,
        'price_per_image': PRICE_PER_IMAGE
    }), 200

# Error handler for 500 errors
@app.errorhandler(500)
def handle_500(error):
    """Custom error handler for server errors."""
    logger.error(f"Server Error: {error}")
    logger.error(traceback.format_exc())
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500

# Modify the main block to be more robust
if __name__ == '__main__':
    # Determine the port
    port = int(os.getenv('PORT', 10000))
    
    # Log port information
    logger.info(f"Attempting to start server on port {port}")
    
    try:
        # Try to create a socket to check port availability
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind(('0.0.0.0', port))
        test_socket.close()
        
        # If socket creation succeeds, run the app
        logger.info(f"Starting Flask development server on 0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.critical(f"Failed to start server on port {port}: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
