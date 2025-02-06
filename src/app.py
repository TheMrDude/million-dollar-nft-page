import os
import uuid
import requests
import json
from flask import Flask, render_template, request, jsonify
from PIL import Image
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__)

# Configuration
MAX_IMAGES = int(os.getenv('MAX_IMAGES', 1000000))
PRICE_PER_IMAGE = float(os.getenv('PRICE_PER_IMAGE', 5.00))
USDC_WALLET_ADDRESS = os.getenv('USDC_WALLET_ADDRESS')
ADMIN_WALLET_ADDRESS = os.getenv('ADMIN_WALLET_ADDRESS')
UPLOAD_FOLDER = os.path.join('src', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

# Initialize SQLite database for tracking payments
def init_db():
    conn = sqlite3.connect('payment_tracker.db')
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

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_payment(tx_hash, wallet_address):
    # TODO: Implement actual blockchain transaction verification
    # This is a placeholder. In a real-world scenario, you'd:
    # 1. Use a blockchain explorer API (like Etherscan for Ethereum)
    # 2. Verify the transaction details:
    #    - Correct recipient wallet
    #    - Correct USDC amount
    #    - Transaction is confirmed
    
    # Simulated verification for demonstration
    conn = sqlite3.connect('payment_tracker.db')
    c = conn.cursor()
    
    # Check if transaction is already processed
    c.execute('SELECT * FROM payments WHERE tx_hash = ?', (tx_hash,))
    if c.fetchone():
        conn.close()
        return False
    
    # Simulate successful payment verification
    c.execute('''
        INSERT INTO payments (tx_hash, amount, wallet_address, status) 
        VALUES (?, ?, ?, ?)
    ''', (tx_hash, PRICE_PER_IMAGE, wallet_address, 'verified'))
    
    conn.commit()
    conn.close()
    
    return True

@app.route('/')
def index():
    uploaded_images = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', 
                           images=uploaded_images, 
                           max_images=MAX_IMAGES,
                           price_per_image=PRICE_PER_IMAGE,
                           usdc_wallet_address=USDC_WALLET_ADDRESS)

@app.route('/verify-payment', methods=['POST'])
def verify_payment_route():
    data = request.json
    tx_hash = data.get('tx_hash')
    wallet_address = data.get('wallet_address')
    
    if not tx_hash or not wallet_address:
        return jsonify({'error': 'Missing transaction hash or wallet address'}), 400
    
    if verify_payment(tx_hash, wallet_address):
        return jsonify({'status': 'Payment verified', 'ready_to_upload': True})
    else:
        return jsonify({'status': 'Payment verification failed'}), 400

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Check total number of images
        if len(os.listdir(UPLOAD_FOLDER)) >= MAX_IMAGES:
            return jsonify({'error': 'Maximum number of images reached'}), 400
        
        # Verify payment before upload
        tx_hash = request.form.get('tx_hash')
        wallet_address = request.form.get('wallet_address')
        
        if not tx_hash or not wallet_address:
            return jsonify({'error': 'Payment not verified'}), 400
        
        # Verify payment
        conn = sqlite3.connect('payment_tracker.db')
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
        
        # Optional: Resize image to a standard size
        with Image.open(filepath) as img:
            img.thumbnail((800, 800))
            img.save(filepath)
        
        # Update payment record with image filename
        conn = sqlite3.connect('payment_tracker.db')
        c = conn.cursor()
        c.execute('UPDATE payments SET image_filename = ? WHERE tx_hash = ?', (filename, tx_hash))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'filename': filename}), 200
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
