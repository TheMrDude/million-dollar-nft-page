import os
import uuid
import requests
import json
import logging
from flask import Flask, render_template, request, jsonify
from PIL import Image
from dotenv import load_dotenv
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Outputs to console
                        logging.FileHandler('/tmp/app.log')  # Outputs to file
                    ])
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
