# Use a minimal Python runtime
FROM python:3.11-alpine3.18

# Install minimal system dependencies
RUN apk add --no-cache \
    build-base \
    linux-headers

# Set working directory
WORKDIR /app

# Copy only essential files
COPY requirements.txt .
COPY src ./src

# Create necessary directories
RUN mkdir -p /tmp/uploads /tmp/database

# Install dependencies with minimal overhead
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Expose port
EXPOSE 10000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/tmp/uploads
ENV DATABASE_PATH=/tmp/database/payment_tracker.db
ENV FLASK_DEBUG=0

# Startup script with minimal configuration
RUN echo '#!/bin/sh\n\
set -e\n\
exec gunicorn \\\n\
    --workers 1 \\\n\
    --threads 2 \\\n\
    --timeout 30 \\\n\
    --bind 0.0.0.0:${PORT:-10000} \\\n\
    --chdir src \\\n\
    --log-level error \\\n\
    app:app\n\
' > /start.sh && chmod +x /start.sh

# Use the startup script
CMD ["/start.sh"]
