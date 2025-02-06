import os
import sys
import uuid
import logging
import sqlite3
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Basic logging configuration
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
MAX_IMAGES = int(os.getenv('MAX_IMAGES', 1000000))
PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', 5.00))
USDC_WALLET_ADDRESS = os.getenv('USDC_WALLET_ADDRESS')

# Ensure upload folder exists
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database path resolution
def get_database_path():
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
        except Exception as e:
            logger.warning(f"Cannot use database path {path}: {e}")
    
    raise RuntimeError("No writable database path found")

# Initialize database
DB_PATH = get_database_path()

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
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
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# Initialize database on startup
init_db()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    try:
        uploaded_images = os.listdir(UPLOAD_FOLDER)
        return render_template('index.html', 
                               images=uploaded_images, 
                               max_images=MAX_IMAGES,
                               price_per_image=PRICE_PER_IMAGE,
                               usdc_wallet_address=USDC_WALLET_ADDRESS)
    except Exception as e:
        logger.error(f"Index route error: {e}")
        return "Server error", 500

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    try:
        data = request.json
        tx_hash = data.get('tx_hash')
        wallet_address = data.get('wallet_address')
        
        if not tx_hash or not wallet_address:
            return jsonify({'error': 'Missing transaction details'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if transaction is already processed
        c.execute('SELECT * FROM payments WHERE tx_hash = ?', (tx_hash,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Transaction already processed'}), 400
        
        # Record payment
        c.execute('''
            INSERT INTO payments (tx_hash, amount, wallet_address, status) 
            VALUES (?, ?, ?, ?)
        ''', (tx_hash, PRICE_PER_IMAGE, wallet_address, 'verified'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'Payment verified', 'ready_to_upload': True})
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Check total number of images
            if len(os.listdir(UPLOAD_FOLDER)) >= MAX_IMAGES:
                return jsonify({'error': 'Maximum number of images reached'}), 400
            
            # Verify payment details
            tx_hash = request.form.get('tx_hash')
            wallet_address = request.form.get('wallet_address')
            
            if not tx_hash or not wallet_address:
                return jsonify({'error': 'Payment not verified'}), 400
            
            # Verify payment in database
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT * FROM payments WHERE tx_hash = ? AND status = "verified"', (tx_hash,))
            payment_record = c.fetchone()
            conn.close()
            
            if not payment_record:
                return jsonify({'error': 'Payment not verified'}), 400
            
            # Generate unique filename
            filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Save file
            file.save(filepath)
            
            return jsonify({'success': True, 'filename': filename}), 200
        
        return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'max_images': MAX_IMAGES,
        'price_per_image': PRICE_PER_IMAGE
    }), 200

@app.errorhandler(500)
def handle_500(error):
    logger.error(f"Server Error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
