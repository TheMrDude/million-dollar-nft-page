# Use a Python runtime
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and source code
COPY requirements.txt .
COPY src ./src

# Create necessary directories
RUN mkdir -p /tmp/uploads /tmp/database

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Expose port
EXPOSE 10000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/tmp/uploads
ENV DATABASE_PATH=/tmp/database/payment_tracker.db

# Startup script
RUN echo '#!/bin/bash\n\
exec gunicorn \\\n\
    --workers 2 \\\n\
    --threads 2 \\\n\
    --timeout 60 \\\n\
    --bind 0.0.0.0:${PORT:-10000} \\\n\
    --chdir src \\\n\
    --log-level warning \\\n\
    app:app\n\
' > /start.sh && chmod +x /start.sh

# Use the startup script
CMD ["/start.sh"]
