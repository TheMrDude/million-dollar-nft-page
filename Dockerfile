# Use a minimal Python runtime
FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    build-base \
    linux-headers \
    curl \
    procps

# Set the working directory in the container
WORKDIR /app

# Copy only necessary files to minimize image size
COPY requirements.txt .
COPY src ./src

# Create necessary directories
RUN mkdir -p /tmp/uploads /tmp/database

# Upgrade pip and install requirements with minimal dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir 'gunicorn[gevent]'

# Expose port
EXPOSE 10000

# Environment variables for resource management
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/tmp/uploads
ENV DATABASE_PATH=/tmp/database/payment_tracker.db
ENV FLASK_DEBUG=0
ENV GUNICORN_CMD_ARGS="--max-requests 250 --max-requests-jitter 50"

# Create a comprehensive startup script
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Print system information\n\
echo "System Information:"\n\
echo "----------------"\n\
free -h\n\
df -h\n\
\n\
# Print Python and package versions\n\
echo "\nPython and Package Versions:"\n\
echo "------------------------"\n\
python --version\n\
pip list\n\
\n\
# Start Gunicorn with strict resource limits\n\
echo "\nStarting Gunicorn..."\n\
exec gunicorn \\\n\
    --worker-class gevent \\\n\
    --workers 1 \\\n\
    --threads 2 \\\n\
    --timeout 60 \\\n\
    --bind 0.0.0.0:${PORT:-10000} \\\n\
    --chdir src \\\n\
    --log-level warning \\\n\
    --limit-request-line 4094 \\\n\
    --limit-request-fields 100 \\\n\
    --limit-request-field-size 8190 \\\n\
    app:app\n\
' > /start.sh && chmod +x /start.sh

# Use the startup script
CMD ["/start.sh"]
