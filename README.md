# The Million Dollar NFT Page 

## Overview
A groundbreaking digital canvas where users can upload their NFTs for $5 USDC per slot.

## Features
- Upload JPEG/PNG NFT images
- Grid-based display supporting up to 1 million images
- Stripe payment integration
- Responsive design
- Advertising space available

## Deployment Instructions

### Local Development
1. Clone the repository
2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Set environment variables in `.env`
5. Run the application
   ```bash
   python src/app.py
   ```

### Render Deployment
1. Fork the repository to your GitHub account
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set the following environment variables:
   - `MAX_IMAGES`: 1000000
   - `PRICE_PER_IMAGE`: 5.00
   - `USDC_WALLET_ADDRESS`: Your USDC wallet address
   - `ADMIN_WALLET_ADDRESS`: Your admin wallet address

## Blockchain Payment Process
- Users send exactly $5 USDC to the specified wallet address
- Enter the transaction hash for verification
- Upload NFT after successful payment verification

## Security Considerations
- Implement robust blockchain transaction verification
- Use secure, audited wallet addresses
- Monitor and log all transactions

## Environment Variables
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
- `MAX_IMAGES`: Maximum number of images (default: 1,000,000)
- `PRICE_PER_IMAGE`: Price per image upload (default: $1.00)

## Future Roadmap
- Multi-blockchain support
- Enhanced payment verification
- Advanced NFT metadata tracking

## Contributing
Pull requests are welcome! Please read our contributing guidelines before submitting.

## License
MIT License
