# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create uploads and database directories
RUN mkdir -p /tmp/uploads /tmp/database

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn
RUN pip install gunicorn

# Expose port (Render will replace this with the dynamic port)
EXPOSE 5000

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV UPLOAD_FOLDER=/tmp/uploads
ENV DATABASE_PATH=/tmp/database/payment_tracker.db

# Use shell form to allow environment variable expansion
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --chdir src app:app
