# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for debugging and building
RUN apt-get update && apt-get install -y \
    net-tools \
    procps \
    iproute2 \
    build-essential \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Create uploads and database directories
RUN mkdir -p /tmp/uploads /tmp/database

# Upgrade pip and install requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir wheel
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Expose port (Render will replace this with the dynamic port)
EXPOSE 10000

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/tmp/uploads
ENV DATABASE_PATH=/tmp/database/payment_tracker.db
ENV FLASK_DEBUG=1

# Create a startup script with more robust error checking
RUN echo '#!/bin/bash\n\
echo "Starting application..."\n\
echo "Current Directory: $(pwd)"\n\
echo "Listing files:"\n\
ls -la src\n\
echo "Python version:"\n\
python --version\n\
echo "Checking app.py exists:"\n\
test -f src/app.py || (echo "ERROR: app.py not found" && exit 1)\n\
echo "Checking requirements installed:"\n\
pip list\n\
echo "Starting Gunicorn..."\n\
exec gunicorn --workers 4 --threads 2 --bind 0.0.0.0:${PORT:-10000} --chdir src app:app\n\
' > /start.sh && chmod +x /start.sh

# Use the startup script
CMD ["/start.sh"]
